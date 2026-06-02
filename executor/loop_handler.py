"""
闭环测试处理器 - 处理需要轮询等待的测试场景
"""
import asyncio
import time
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from config import LOGIN_USERNAME, LOGIN_PASSWORD


class LoopHandler:
    """处理闭环测试的轮询和截图"""

    def __init__(self, page, tracker, system_url):
        self.page = page
        self.tracker = tracker
        self.system_url = system_url
        self.screenshots_dir = Path(__file__).parent.parent / "screenshots"
        self.screenshots_dir.mkdir(exist_ok=True)

    async def wait_for_report_generation(self, case_id, max_wait_seconds=3600, poll_interval=5):
        """
        轮询等待报告生成 - 打开可见浏览器窗口实时监控对话框内容

        Args:
            case_id: 用例ID，用于查找对话
            max_wait_seconds: 最长等待时间（秒），默认1小时
            poll_interval: 轮询间隔（秒）

        Returns:
            (success: bool, message: str, screenshot_path: str)
        """
        start_time = time.time()
        poll_count = 0

        self.tracker.record_step("wait_for_report", "polling_start", "pending", {
            "max_wait": max_wait_seconds,
            "poll_interval": poll_interval,
            "case_id": case_id
        })

        # 打开新的可见浏览器窗口用于监控
        print("\n📺 打开监控浏览器窗口...")
        monitor_playwright = await async_playwright().start()
        monitor_browser = await monitor_playwright.chromium.launch(headless=False)
        monitor_page = await monitor_browser.new_page()
        monitor_page.set_default_timeout(30000)

        try:
            while time.time() - start_time < max_wait_seconds:
                poll_count += 1
                elapsed = round(time.time() - start_time, 1)

                print(f"\n[轮询 #{poll_count}] 已等待 {elapsed}s，检查对话框内容...")

                # 记录轮询步骤
                self.tracker.record_step("poll_report", f"poll_{poll_count}", "pending", {
                    "elapsed_seconds": elapsed
                })

                # 导航到决策对话页面
                await monitor_page.goto(f"{self.system_url}/decision", wait_until="domcontentloaded")
                await monitor_page.wait_for_timeout(1000)

                # 点击最新的对话卡片
                await monitor_page.evaluate('''() => {
                    const cards = Array.from(document.querySelectorAll('*')).filter(el => {
                        const text = el.textContent;
                        return text && text.includes('引流号') && text.length < 150;
                    });

                    if (cards.length > 0) {
                        cards[0].click();
                    }
                }''')

                await monitor_page.wait_for_timeout(500)

                # 获取对话框内容
                dialog_content = await monitor_page.evaluate('() => document.body.innerText')

                if dialog_content:
                    print(f"  ✓ 获取到对话框内容 ({len(dialog_content)} 字符)")

                    # 检查完成信号
                    result = self._check_completion_signal(dialog_content)

                    if result["completed"]:
                        print(f"✓ {result['message']}")

                        # 截图保存
                        screenshot_path = await self._take_screenshot_from_page(monitor_page, f"report_generated_{poll_count}")

                        self.tracker.record_step("poll_report", f"poll_{poll_count}", "success", {
                            "signal": result["signal"],
                            "message": result["message"],
                            "elapsed_seconds": elapsed,
                            "screenshot": str(screenshot_path)
                        })

                        self.tracker.record_step("wait_for_report", "polling_complete", result["status"], {
                            "total_polls": poll_count,
                            "total_time": elapsed,
                            "signal": result["signal"],
                            "message": result["message"]
                        })

                        return result["status"] == "success", result["message"], screenshot_path

                self.tracker.record_step("poll_report", f"poll_{poll_count}", "success", {
                    "elapsed_seconds": elapsed,
                    "completed": False
                })

                # 等待后再轮询
                print(f"  未检测到完成信号，{poll_interval}s 后继续检查...")
                await asyncio.sleep(poll_interval)

            # 超时
            print(f"✗ 等待超时！已轮询 {poll_count} 次，总耗时 {max_wait_seconds}s")

            # 超时时也截图
            screenshot_path = await self._take_screenshot_from_page(monitor_page, f"timeout_poll_{poll_count}")

            self.tracker.record_step("wait_for_report", "polling_timeout", "failed", {
                "total_polls": poll_count,
                "max_wait": max_wait_seconds,
                "screenshot": str(screenshot_path)
            })

            return False, "Report generation timeout", screenshot_path

        finally:
            # 关闭监控浏览器
            await monitor_page.close()
            await monitor_browser.close()
            await monitor_playwright.stop()

    async def _get_dialog_content(self, case_id):
        """获取对话框内容 - 使用已打开的页面"""
        try:
            # 先刷新页面以确保获取最新内容
            await self.page.reload(wait_until="domcontentloaded")
            await self.page.wait_for_timeout(1000)

            # 点击最新的对话卡片，使右侧显示对话内容
            await self.page.evaluate('''() => {
                const cards = Array.from(document.querySelectorAll('*')).filter(el => {
                    const text = el.textContent;
                    return text && text.includes('引流号') && text.length < 150;
                });

                if (cards.length > 0) {
                    cards[0].click();
                }
            }''')

            await self.page.wait_for_timeout(500)

            # 获取页面文本（现在右侧应该显示对话内容了）
            page_text = await self.page.evaluate('() => document.body.innerText')
            return page_text

        except Exception as e:
            print(f"  获取对话框内容出错: {e}")
            return None

    def _check_completion_signal(self, content):
        """检查对话框内容中的完成信号"""

        # 成功信号
        if "MarketingAI任务执行报告" in content or "MarketingAI 任务执行报告" in content:
            return {
                "completed": True,
                "status": "success",
                "signal": "report_generated",
                "message": "报告已生成"
            }

        # 失败信号 - 规划失败
        if "规划阶段出错" in content or "规划失败" in content:
            return {
                "completed": True,
                "status": "failed",
                "signal": "planning_error",
                "message": "规划阶段出错"
            }

        # 失败信号 - 服务错误
        if "Error code: 500" in content or "Relay service error" in content:
            return {
                "completed": True,
                "status": "failed",
                "signal": "service_error",
                "message": "服务错误 (500)"
            }

        # 失败信号 - 其他错误
        if "出错" in content or "失败" in content or "error" in content.lower():
            # 但要排除"未生成"这样的中间状态
            if "报告未生成" not in content and "未生成" not in content:
                return {
                    "completed": True,
                    "status": "failed",
                    "signal": "error",
                    "message": "执行出错"
                }

        # 未完成
        return {
            "completed": False,
            "status": None,
            "signal": None,
            "message": None
        }

    async def _check_report_generated(self):
        """检查对话框中是否有执行报告"""
        try:
            # 获取页面文本
            page_text = await self.page.evaluate('() => document.body.innerText')

            # 只检查是否有"MarketingAI任务执行报告"标题（支持有无空格）
            # 这是唯一可靠的报告标识
            if page_text and ("MarketingAI任务执行报告" in page_text or "MarketingAI 任务执行报告" in page_text):
                return True

            return False
        except Exception as e:
            print(f"  检查报告时出错: {e}")
            return False

    async def _get_report_url(self):
        """获取报告链接"""
        try:
            # 查找报告链接
            report_link = await self.page.query_selector('a[href*="report"]')
            if report_link:
                url = await report_link.get_attribute('href')
                if url:
                    if not url.startswith('http'):
                        url = f"{self.system_url}{url}"
                    return url

            # 如果没有找到链接，返回当前页面 URL
            return self.page.url
        except:
            return self.page.url

    async def _take_screenshot(self, name):
        """截图保存"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = self.screenshots_dir / filename

            await self.page.screenshot(path=str(filepath))
            print(f"  📸 截图已保存: {filepath}")

            return filepath
        except Exception as e:
            print(f"  ✗ 截图失败: {e}")
            return None

    async def _take_screenshot_from_page(self, page, name):
        """从指定页面截图保存"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            filepath = self.screenshots_dir / filename

            await page.screenshot(path=str(filepath))
            print(f"  📸 截图已保存: {filepath}")

            return filepath
        except Exception as e:
            print(f"  ✗ 截图失败: {e}")
            return None

    async def test_closedloop(self, case, result, tracker):
        """
        通用闭环测试处理器

        流程:
        1. 导航到决策对话页面
        2. 点击一个决策对话进入
        3. 点击"新建对话"按钮
        4. 在下方对话框中输入指令
        5. 轮询等待执行报告生成（直接监控对话框内容）
        6. 截图保存报告
        """
        desc = case.get("description", "")
        instruction = case.get("instruction", "")
        case_id = case.get("case_id", "")

        if not instruction:
            result["status"] = "FAIL"
            result["error_msg"] = "No instruction provided in case"
            tracker.record_step("input_instruction", "instruction", "failed")
            tracker.set_result("failed", "No instruction provided in case")
            return

        # 导航到决策对话页面
        tracker.record_step("navigate", "/decision", "pending")
        await self.page.goto(f"{self.system_url}/decision", wait_until="domcontentloaded")
        await self.page.wait_for_timeout(2000)
        tracker.record_step("navigate", "/decision", "success")

        # 查找并点击第一个决策对话
        tracker.record_step("find_element", "decision_item", "pending")
        decision_items = await self.page.query_selector_all('[class*="decision"], [class*="item"], tr, li')

        if not decision_items or len(decision_items) == 0:
            result["status"] = "FAIL"
            result["error_msg"] = "No decision items found"
            tracker.record_step("find_element", "decision_item", "failed")
            tracker.set_result("failed", "No decision items found")
            return

        tracker.record_step("find_element", "decision_item", "success")

        # 点击第一个决策对话
        tracker.record_step("click", "decision_item", "pending")
        await decision_items[0].click()
        await self.page.wait_for_timeout(2000)
        tracker.record_step("click", "decision_item", "success")

        # 查找并点击"新建对话"按钮
        tracker.record_step("find_element", "create_dialog_button", "pending")
        buttons = await self.page.query_selector_all('button')
        create_dialog_btn = None

        for btn in buttons:
            text = await btn.text_content()
            if "新建对话" in text or "新建" in text:
                create_dialog_btn = btn
                break

        if not create_dialog_btn:
            result["status"] = "FAIL"
            result["error_msg"] = "Create dialog button not found"
            tracker.record_step("find_element", "create_dialog_button", "failed")
            tracker.set_result("failed", "Create dialog button not found")
            return

        tracker.record_step("find_element", "create_dialog_button", "success")

        # 点击新建对话按钮
        tracker.record_step("click", "create_dialog_button", "pending")
        await create_dialog_btn.click()
        await self.page.wait_for_timeout(2000)
        tracker.record_step("click", "create_dialog_button", "success")

        # 等待对话框出现
        tracker.record_step("wait_for_dialog", "dialog_load", "pending")
        try:
            await self.page.wait_for_selector('input[type="text"], textarea, [contenteditable="true"]', timeout=5000)
            tracker.record_step("wait_for_dialog", "dialog_load", "success")
        except:
            tracker.record_step("wait_for_dialog", "dialog_load", "skipped")
            pass

        # 查找对话框的输入框
        tracker.record_step("find_element", "chat_input", "pending")
        dialog_inputs = await self.page.query_selector_all('input[type="text"], textarea, [contenteditable="true"]')

        if not dialog_inputs or len(dialog_inputs) == 0:
            result["status"] = "FAIL"
            result["error_msg"] = "Chat input not found"
            tracker.record_step("find_element", "chat_input", "failed")
            tracker.set_result("failed", "Chat input not found")
            return

        tracker.record_step("find_element", "chat_input", "success")

        # 使用最后一个输入元素（对话框输入框）
        chat_input = dialog_inputs[-1]

        # 输入指令
        tracker.record_step("input_instruction", "instruction", "pending")

        try:
            await chat_input.scroll_into_view_if_needed()
            await self.page.wait_for_timeout(300)
            await chat_input.focus()
            await self.page.wait_for_timeout(300)

            await chat_input.type(instruction, delay=50)
            await self.page.wait_for_timeout(500)
            tracker.record_step("input_instruction", "instruction", "success", {"instruction": instruction})

            # 发送指令（按Enter）
            tracker.record_step("send_instruction", "send_button", "pending")
            await chat_input.press("Enter")
            await self.page.wait_for_timeout(1500)
            tracker.record_step("send_instruction", "send_button", "success")

        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = f"Input error: {str(e)[:50]}"
            tracker.record_step("input_instruction", "instruction", "failed")
            tracker.set_result("failed", f"Input error: {str(e)[:50]}")
            return

        # 开始轮询等待报告生成（直接监控对话框内容）
        print("\n🔄 开始轮询等待执行报告生成...")
        success, message, screenshot_path = await self.wait_for_report_generation(
            case_id=case_id,
            max_wait_seconds=3600,  # 最多等待 1 小时
            poll_interval=300  # 每 5 分钟检查一次
        )

        if success:
            result["status"] = "PASS"
            result["error_msg"] = ""
            tracker.set_result("success", {
                "message": message,
                "screenshot": str(screenshot_path)
            })
        else:
            result["status"] = "FAIL"
            result["error_msg"] = message
            tracker.set_result("failed", message)

    async def test_kol_loop(self, case, result, tracker):
        """向后兼容的 KOL 闭环测试方法"""
        await self.test_closedloop(case, result, tracker)
