#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闭环监控模块 - 实时监控对话框内容
"""
import asyncio
import time
from datetime import datetime
from pathlib import Path


class LoopMonitor:
    """闭环实时监控器"""

    def __init__(self, system_url, screenshots_dir="screenshots"):
        self.system_url = system_url
        self.screenshots_dir = Path(screenshots_dir)
        self.screenshots_dir.mkdir(exist_ok=True)
        self.check_count = 0
        self.start_time = None

    async def start_monitoring(self, page, check_interval=300, max_wait=3600, instruction=None):
        """
        开始监控对话框内容

        Args:
            page: Playwright 页面对象
            check_interval: 检查间隔（秒），默认5分钟
            max_wait: 最长等待时间（秒），默认1小时
            instruction: 当前闭环的指令文本，用于精准定位对话卡片

        Returns:
            (success: bool, content: str, screenshot_path: str, elapsed_time: int)
        """
        self.start_time = time.time()
        self.check_count = 0

        print("\n" + "=" * 60)
        print("🔄 开始实时监控对话框内容")
        print("=" * 60)

        while time.time() - self.start_time < max_wait:
            self.check_count += 1
            elapsed = round(time.time() - self.start_time, 1)

            print(f"\n[检查 #{self.check_count}] 已等待 {elapsed}s")

            # 导航到决策对话页面
            await page.goto(f"{self.system_url}/decision", wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            # 等待卡片渲染后再点击（用指令前缀精准匹配对应的对话卡片）
            card_prefix = instruction[:10] if instruction else None
            if card_prefix:
                clicked = await page.evaluate('''async (prefix) => {
                    // 最多等 10 秒让卡片出现
                    for (let i = 0; i < 20; i++) {
                        const cards = Array.from(document.querySelectorAll('*')).filter(el => {
                            const text = el.textContent;
                            return text && text.includes(prefix) && text.length < 200;
                        });
                        if (cards.length > 0) {
                            // 取文本最短的那个（最精确的叶子元素）
                            cards.sort((a, b) => a.textContent.length - b.textContent.length);
                            cards[0].click();
                            return true;
                        }
                        await new Promise(r => setTimeout(r, 500));
                    }
                    return false;
                }''', card_prefix)
            else:
                # 兜底：点击左侧列表第一个卡片（按位置）
                clicked = await page.evaluate('''async () => {
                    for (let i = 0; i < 20; i++) {
                        const cards = Array.from(document.querySelectorAll('*')).filter(el => {
                            const rect = el.getBoundingClientRect();
                            return rect.left < 350 && rect.height > 50 && rect.height < 150
                                && rect.width > 150 && el.textContent.length > 5
                                && el.textContent.length < 200;
                        });
                        // 按垂直位置排序，取第一个（跳过"新建对话"按钮区域）
                        cards.sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top);
                        const valid = cards.filter(el => el.getBoundingClientRect().top > 160);
                        if (valid.length > 0) {
                            valid[0].click();
                            return true;
                        }
                        await new Promise(r => setTimeout(r, 500));
                    }
                    return false;
                }''')

            await page.wait_for_timeout(500)

            # 获取对话框内容
            content = await page.evaluate('() => document.body.innerText')

            if content:
                # 检查完成信号
                result = self._check_completion_signal(content)

                if result["completed"]:
                    print(f"✓ {result['message']}")

                    # 截图保存
                    screenshot_path = await self._take_screenshot(page, f"report_{self.check_count}")

                    print(f"✅ 监控完成！")
                    print(f"   状态：{result['status']}")
                    print(f"   耗时：{elapsed}s")
                    print(f"   检查次数：{self.check_count}")

                    return result["status"] == "success", content, screenshot_path, elapsed, result["message"]

            print(f"  ⏳ 未检测到完成信号，{check_interval}s 后继续检查...")
            await asyncio.sleep(check_interval)

        # 超时
        print(f"\n✗ 监控超时！已检查 {self.check_count} 次，总耗时 {max_wait}s")
        screenshot_path = await self._take_screenshot(page, f"timeout_{self.check_count}")

        return False, "", screenshot_path, max_wait, "监控超时"

    def _check_completion_signal(self, content):
        """检查对话框内容中的完成信号"""

        # 成功信号
        if "任务执行报告" in content:
            return {
                "completed": True,
                "status": "success",
                "message": "报告已生成"
            }

        # 失败信号 - 规划失败
        if "规划阶段出错" in content or "规划失败" in content:
            return {
                "completed": True,
                "status": "failed",
                "message": "规划阶段出错"
            }

        # 失败信号 - 服务错误
        if "Error code: 500" in content or "Relay service error" in content:
            return {
                "completed": True,
                "status": "failed",
                "message": "服务错误 (500)"
            }

        # 失败信号 - 报告生成失败
        if "报告生成失败" in content:
            return {
                "completed": True,
                "status": "failed",
                "message": "报告生成失败"
            }

        # 失败信号 - 模型不可用
        if "model_not_found" in content or "No available channel" in content:
            return {
                "completed": True,
                "status": "failed",
                "message": "模型不可用"
            }

        # 失败信号 - AI服务不可用
        if "AI 服务暂时不可用" in content or "AI服务暂时不可用" in content:
            return {
                "completed": True,
                "status": "failed",
                "message": "AI服务暂时不可用"
            }

        # 未完成
        return {
            "completed": False,
            "status": None,
            "message": None
        }

    async def _take_screenshot(self, page, name):
        """截图保存"""
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
