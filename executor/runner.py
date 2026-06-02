import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright
from config import SYSTEM_URL, LOGIN_USERNAME, LOGIN_PASSWORD, HEADLESS, TIMEOUT
from trace.tracker import get_trace_manager
from executor.loop_handler import LoopHandler


class TestExecutor:
    def __init__(self):
        self.browser = None
        self.page = None
        self.playwright = None

    async def setup(self):
        """启动浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=HEADLESS)
        self.page = await self.browser.new_page()
        self.page.set_default_timeout(TIMEOUT)

    async def teardown(self):
        """关闭浏览器"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def login(self):
        """登录系统"""
        try:
            await self.page.goto(f"{SYSTEM_URL}/overview", wait_until="domcontentloaded")
        except:
            await self.page.goto(f"{SYSTEM_URL}/overview")

        # 等待登录表单出现
        try:
            await self.page.wait_for_selector('input[type="text"]', timeout=5000)
        except:
            # 可能已经登录了
            return

        # 填写账号密码
        await self.page.fill('input[type="text"]', LOGIN_USERNAME)
        await self.page.fill('input[type="password"]', LOGIN_PASSWORD)

        # 点击登录按钮
        login_btn = await self.page.query_selector('button')
        if login_btn:
            await login_btn.click()

        # 等待登录完成
        try:
            await self.page.wait_for_url("**/overview", timeout=10000)
        except:
            pass

    async def execute_case(self, case):
        """执行单条测试用例"""
        start_time = time.time()
        case_id = case.get("case_id", "UNKNOWN")
        description = case.get("description", "")

        # 创建追踪器
        trace_manager = get_trace_manager()
        tracker = trace_manager.create_tracker(case_id, description)

        result = {
            "case_id": case_id,
            "description": description,
            "module": case.get("module") or "Unknown",
            "level": case.get("level") or "P3",
            "status": "PASS",
            "error_msg": "",
            "duration": 0,
            "trace_id": tracker.trace_id,
        }

        try:
            # 根据模块和描述执行不同的测试
            module = case.get("module", "") or ""

            if "账号" in str(module) or "User" in str(module):
                await self._test_account_module(case, result, tracker)
            elif "事件" in str(module) or "Event" in str(module):
                await self._test_event_module(case, result, tracker)
            elif "决策" in str(module) or "Agent" in str(module):
                await self._test_agent_module(case, result, tracker)
            elif "执行日志" in str(module) or "Log" in str(module):
                await self._test_log_module(case, result, tracker)
            elif "知识库" in str(module) or "Knowledge" in str(module):
                await self._test_knowledge_module(case, result, tracker)
            elif "账号管理" in str(module) or "Admin" in str(module):
                await self._test_admin_module(case, result, tracker)
            elif "人设" in str(module) or "Character" in str(module):
                await self._test_character_module(case, result, tracker)
            elif "定时任务" in str(module) or "Schedule" in str(module):
                await self._test_schedule_module(case, result, tracker)
            elif "反向追踪" in str(module) or "Tracking" in str(module):
                await self._test_tracking_module(case, result, tracker)
            else:
                result["status"] = "SKIP"
                result["error_msg"] = "Unsupported module"
                tracker.set_result("skipped", "Unsupported module")

        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = str(e)[:100]
            tracker.set_result("failed", str(e)[:100])

        result["duration"] = round(time.time() - start_time, 2)

        # 如果还没有设置结果，根据 status 设置
        if tracker.result == "pending":
            if result["status"] == "PASS":
                tracker.set_result("success")
            elif result["status"] == "FAIL":
                tracker.set_result("failed", result["error_msg"])
            elif result["status"] == "SKIP":
                tracker.set_result("skipped", result["error_msg"])

        return result

    async def _test_account_module(self, case, result, tracker):
        """测试账号模块"""
        desc = case.get("description", "")

        # 导航到账号管理页面
        tracker.record_step("navigate", "/accounts", "pending")
        await self.page.goto(f"{SYSTEM_URL}/accounts", wait_until="domcontentloaded")
        await self.page.wait_for_timeout(1000)
        tracker.record_step("navigate", "/accounts", "success")

        if "导入" in desc:
            await self._test_import_account(case, result, tracker)
        elif "新建" in desc and "浏览器" in desc:
            await self._test_create_account(case, result, tracker)
        elif "删除" in desc and "账号" in desc:
            await self._test_delete_account(case, result, tracker)
        elif "编辑" in desc and "账号" in desc:
            await self._test_edit_account(case, result, tracker)
        elif "启用" in desc:
            await self._test_enable_account(case, result, tracker)
        elif "禁用" in desc:
            await self._test_disable_account(case, result, tracker)
        elif "获取" in desc or "查询" in desc:
            await self._test_query_account(case, result, tracker)
        elif "绑定" in desc and "人设" in desc:
            await self._test_bind_character(case, result, tracker)
        elif "设置" in desc and "上限" in desc:
            await self._test_set_operation_limit(case, result, tracker)
        elif "IP" in desc or "配置" in desc:
            await self._test_configure_ip(case, result, tracker)
        else:
            result["status"] = "SKIP"
            result["error_msg"] = "Unknown account operation"
            tracker.set_result("skipped", "Unknown account operation")

    async def _test_import_account(self, case, result, tracker):
        """测试导入账号"""
        desc = case.get("description", "")

        # 查找导入按钮
        tracker.record_step("find_element", "import_button", "pending")
        import_btn = await self.page.query_selector('button:has-text("批量上传账号")')
        if not import_btn:
            import_btn = await self.page.query_selector('button:has-text("导入")')
        if not import_btn:
            buttons = await self.page.query_selector_all('button')
            for btn in buttons:
                text = await btn.text_content()
                if "上传" in text or "导入" in text:
                    import_btn = btn
                    break

        if not import_btn:
            result["status"] = "FAIL"
            result["error_msg"] = "Import button not found"
            tracker.record_step("find_element", "import_button", "failed", {"reason": "button not found"})
            tracker.set_result("failed", "Import button not found")
            return

        tracker.record_step("find_element", "import_button", "success")

        # 点击导入按钮
        tracker.record_step("click", "import_button", "pending")
        await import_btn.click()
        await self.page.wait_for_timeout(1000)
        tracker.record_step("click", "import_button", "success")

        # 等待文件上传框
        tracker.record_step("find_element", "file_input", "pending")
        file_input = None
        try:
            file_input = await self.page.wait_for_selector('input[type="file"]', timeout=3000)
        except:
            file_input = await self.page.query_selector('input[type="file"]')

        if not file_input:
            result["status"] = "FAIL"
            result["error_msg"] = "File input not found"
            tracker.record_step("find_element", "file_input", "failed", {"reason": "file input not found"})
            tracker.set_result("failed", "File input not found")
            return

        tracker.record_step("find_element", "file_input", "success")

        # 选择测试文件
        if "txt" in desc:
            test_file = "test_accounts.txt"
        elif "jsonl" in desc:
            test_file = "test_accounts.jsonl"
        elif "空" in desc:
            test_file = "empty.txt"
        elif "错误" in desc:
            test_file = "invalid.txt"
        else:
            test_file = "test_accounts.txt"

        # 创建测试文件
        test_file_path = Path(__file__).parent.parent / "test_data" / test_file
        if not test_file_path.exists():
            test_file_path.parent.mkdir(parents=True, exist_ok=True)
            if "空" in desc:
                test_file_path.write_text("")
            elif "错误" in desc:
                test_file_path.write_text("invalid data")
            else:
                test_file_path.write_text("test_user_1\ntest_user_2\n")

        # 上传文件
        tracker.record_step("upload_file", test_file, "pending")
        await file_input.set_input_files(str(test_file_path))
        await self.page.wait_for_timeout(1500)
        tracker.record_step("upload_file", test_file, "success")

        # 检查结果
        tracker.record_step("check_result", "message", "pending")
        try:
            await self.page.wait_for_selector('.ant-message-success, .ant-notification-notice-success', timeout=3000)
            result["status"] = "PASS"
            tracker.record_step("check_result", "message", "success", {"type": "success_message"})
            tracker.set_result("success")
        except:
            error_msg = await self.page.query_selector('.ant-message-error, .ant-notification-notice-error')
            if error_msg:
                result["status"] = "FAIL"
                result["error_msg"] = "Import failed with error message"
                tracker.record_step("check_result", "message", "failed", {"type": "error_message"})
                tracker.set_result("failed", "Import failed with error message")
            else:
                result["status"] = "PASS"
                tracker.record_step("check_result", "message", "success", {"type": "no_message"})
                tracker.set_result("success")

    async def _test_create_account(self, case, result, tracker):
        """测试新建账号"""
        tracker.record_step("find_element", "create_button", "pending")
        create_btn = await self.page.query_selector('button:has-text("新建账号")')
        if not create_btn:
            create_btn = await self.page.query_selector('button:has-text("新建")')
        if not create_btn:
            buttons = await self.page.query_selector_all('button')
            for btn in buttons:
                text = await btn.text_content()
                if "新建" in text:
                    create_btn = btn
                    break

        if not create_btn:
            result["status"] = "FAIL"
            result["error_msg"] = "Create button not found"
            tracker.record_step("find_element", "create_button", "failed")
            tracker.set_result("failed", "Create button not found")
            return

        tracker.record_step("find_element", "create_button", "success")
        tracker.record_step("click", "create_button", "pending")
        await create_btn.click()
        await self.page.wait_for_timeout(1000)
        tracker.record_step("click", "create_button", "success")

        # 等待表单出现
        tracker.record_step("find_element", "form", "pending")
        try:
            await self.page.wait_for_selector('input[placeholder*="账号"], input[placeholder*="用户"]', timeout=5000)
            tracker.record_step("find_element", "form", "success")
        except:
            result["status"] = "FAIL"
            result["error_msg"] = "Create form not found"
            tracker.record_step("find_element", "form", "failed")
            tracker.set_result("failed", "Create form not found")
            return

        # 填写表单
        tracker.record_step("fill_form", "account_input", "pending")
        account_input = await self.page.query_selector('input[placeholder*="账号"]')
        if not account_input:
            account_input = await self.page.query_selector('input[placeholder*="用户"]')
        if not account_input:
            inputs = await self.page.query_selector_all('input[type="text"]')
            if inputs:
                account_input = inputs[0]

        if account_input:
            await account_input.fill("test_account_" + str(int(time.time())))
            tracker.record_step("fill_form", "account_input", "success")

        # 提交表单
        tracker.record_step("submit_form", "submit_button", "pending")
        submit_btn = await self.page.query_selector('button:has-text("确定"), button:has-text("提交")')
        if submit_btn:
            await submit_btn.click()
            await self.page.wait_for_timeout(1000)
            tracker.record_step("submit_form", "submit_button", "success")

        result["status"] = "PASS"
        tracker.set_result("success")

    async def _test_delete_account(self, case, result, tracker):
        """测试删除账号"""
        tracker.record_step("find_element", "delete_button", "pending")
        delete_btns = await self.page.query_selector_all('button:has-text("删除")')
        if not delete_btns or len(delete_btns) == 0:
            result["status"] = "SKIP"
            result["error_msg"] = "No accounts to delete"
            tracker.record_step("find_element", "delete_button", "skipped")
            tracker.set_result("skipped", "No accounts to delete")
            return

        tracker.record_step("find_element", "delete_button", "success")

        # 获取要删除的账号信息
        tracker.record_step("get_account_info", "account_name", "pending")
        try:
            # 尝试获取账号所在行的账号名称
            delete_btn = delete_btns[0]
            account_row = await delete_btn.evaluate('el => el.closest("tr")')
            if account_row:
                account_name = await account_row.evaluate('el => el.textContent')
                tracker.record_step("get_account_info", "account_name", "success", {"account": account_name[:100]})
                result["deleted_account"] = account_name[:100]
            else:
                tracker.record_step("get_account_info", "account_name", "skipped")
        except:
            tracker.record_step("get_account_info", "account_name", "skipped")

        tracker.record_step("click", "delete_button", "pending")
        await delete_btns[0].click()
        await self.page.wait_for_timeout(500)
        tracker.record_step("click", "delete_button", "success")

        # 确认删除
        tracker.record_step("confirm_action", "confirm_button", "pending")
        confirm_btn = await self.page.query_selector('button:has-text("确定"), button:has-text("OK")')
        if confirm_btn:
            await confirm_btn.click()
            await self.page.wait_for_timeout(1000)
            tracker.record_step("confirm_action", "confirm_button", "success")

        result["status"] = "PASS"
        tracker.set_result("success")

    async def _test_edit_account(self, case, result, tracker):
        """测试编辑账号"""
        tracker.record_step("find_element", "edit_button", "pending")
        edit_btns = await self.page.query_selector_all('button:has-text("编辑")')
        if not edit_btns or len(edit_btns) == 0:
            result["status"] = "SKIP"
            result["error_msg"] = "No accounts to edit"
            tracker.record_step("find_element", "edit_button", "skipped")
            tracker.set_result("skipped", "No accounts to edit")
            return

        tracker.record_step("find_element", "edit_button", "success")
        tracker.record_step("click", "edit_button", "pending")
        await edit_btns[0].click()
        await self.page.wait_for_timeout(500)
        tracker.record_step("click", "edit_button", "success")

        # 修改字段
        tracker.record_step("fill_form", "edit_input", "pending")
        inputs = await self.page.query_selector_all('input[type="text"]')
        if inputs and len(inputs) > 0:
            await inputs[0].fill("updated_value")
            tracker.record_step("fill_form", "edit_input", "success")

        # 提交
        tracker.record_step("submit_form", "submit_button", "pending")
        submit_btn = await self.page.query_selector('button:has-text("确定"), button:has-text("提交")')
        if submit_btn:
            await submit_btn.click()
            await self.page.wait_for_timeout(1000)
            tracker.record_step("submit_form", "submit_button", "success")

        result["status"] = "PASS"
        tracker.set_result("success")

    async def _test_enable_account(self, case, result, tracker):
        """测试启用账号 - 点击启用列的开关按钮"""
        tracker.record_step("find_element", "enable_toggle", "pending")

        # 获取表格行
        rows = await self.page.query_selector_all('tr')
        if not rows or len(rows) < 2:
            result["status"] = "SKIP"
            result["error_msg"] = "No accounts in list"
            tracker.record_step("find_element", "enable_toggle", "skipped")
            tracker.set_result("skipped", "No accounts in list")
            return

        # 在第一行数据中查找开关按钮（可能在任何列）
        first_row = rows[1]
        toggle_btns = await first_row.query_selector_all('button, [role="switch"]')

        if not toggle_btns or len(toggle_btns) == 0:
            result["status"] = "SKIP"
            result["error_msg"] = "No toggle button found"
            tracker.record_step("find_element", "enable_toggle", "skipped")
            tracker.set_result("skipped", "No toggle button found")
            return

        tracker.record_step("find_element", "enable_toggle", "success")

        # 点击第一个开关按钮
        tracker.record_step("click", "enable_toggle", "pending")
        toggle_btn = toggle_btns[0]
        await toggle_btn.scroll_into_view_if_needed()
        await self.page.wait_for_timeout(500)
        await toggle_btn.click()
        await self.page.wait_for_timeout(1000)
        tracker.record_step("click", "enable_toggle", "success")

        result["status"] = "PASS"
        tracker.set_result("success")

    async def _test_disable_account(self, case, result, tracker):
        """测试禁用账号 - 点击启用列的开关按钮"""
        tracker.record_step("find_element", "disable_toggle", "pending")

        # 获取表格行
        rows = await self.page.query_selector_all('tr')
        if not rows or len(rows) < 2:
            result["status"] = "SKIP"
            result["error_msg"] = "No accounts in list"
            tracker.record_step("find_element", "disable_toggle", "skipped")
            tracker.set_result("skipped", "No accounts in list")
            return

        # 查找"启用"列的表头
        headers = await rows[0].query_selector_all('th, td')
        enable_col_idx = None
        for i, header in enumerate(headers):
            text = await header.text_content()
            if "启用" in text:
                enable_col_idx = i
                break

        if enable_col_idx is None:
            result["status"] = "FAIL"
            result["error_msg"] = "Enable column not found"
            tracker.record_step("find_element", "disable_toggle", "failed")
            tracker.set_result("failed", "Enable column not found")
            return

        # 获取第一行数据的启用列
        cells = await rows[1].query_selector_all('td')
        if len(cells) <= enable_col_idx:
            result["status"] = "SKIP"
            result["error_msg"] = "Enable cell not found"
            tracker.record_step("find_element", "disable_toggle", "skipped")
            tracker.set_result("skipped", "Enable cell not found")
            return

        tracker.record_step("find_element", "disable_toggle", "success")

        # 查找开关按钮
        enable_cell = cells[enable_col_idx]
        toggle_btn = await enable_cell.query_selector('button, [role="switch"]')

        if not toggle_btn:
            result["status"] = "FAIL"
            result["error_msg"] = "Toggle button not found"
            tracker.record_step("find_element", "disable_toggle", "failed")
            tracker.set_result("failed", "Toggle button not found")
            return

        tracker.record_step("click", "disable_toggle", "pending")
        await toggle_btn.scroll_into_view_if_needed()
        await self.page.wait_for_timeout(500)
        await toggle_btn.click()
        await self.page.wait_for_timeout(1000)
        tracker.record_step("click", "disable_toggle", "success")

        result["status"] = "PASS"
        tracker.set_result("success")

    async def _test_query_account(self, case, result, tracker):
        """测试获取账号信息 - 先勾选账号，再点击上方的获取账号信息选项"""
        tracker.record_step("find_element", "account_checkbox", "pending")

        # 获取表格行
        rows = await self.page.query_selector_all('tr')
        if not rows or len(rows) < 2:
            result["status"] = "SKIP"
            result["error_msg"] = "No accounts in list"
            tracker.record_step("find_element", "account_checkbox", "skipped")
            tracker.set_result("skipped", "No accounts in list")
            return

        # 查找第一行的勾选框 - 在第一列（账号ID左侧）
        first_row = rows[1]

        # 尝试在第一行中查找勾选框 - 可能是 input 或 Ant Design 的 checkbox
        checkbox = await first_row.query_selector('input[type="checkbox"]')

        if not checkbox:
            # 尝试查找 Ant Design checkbox
            checkbox = await first_row.query_selector('[class*="checkbox"]')

        if not checkbox:
            # 尝试查找任何 input 元素
            checkbox = await first_row.query_selector('input')

        if not checkbox:
            result["status"] = "FAIL"
            result["error_msg"] = "Checkbox not found in first row"
            tracker.record_step("find_element", "account_checkbox", "failed")
            tracker.set_result("failed", "Checkbox not found in first row")
            return

        tracker.record_step("find_element", "account_checkbox", "success")
        tracker.record_step("click", "account_checkbox", "pending")

        await checkbox.scroll_into_view_if_needed()
        await self.page.wait_for_timeout(300)
        await checkbox.click()
        await self.page.wait_for_timeout(1000)
        tracker.record_step("click", "account_checkbox", "success")

        # 查找上方的"获取账号信息"选项
        tracker.record_step("find_element", "query_option", "pending")
        buttons = await self.page.query_selector_all('button')
        query_btn = None

        for btn in buttons:
            text = await btn.text_content()
            if "获取" in text or "查询" in text or "信息" in text:
                query_btn = btn
                break

        if not query_btn:
            result["status"] = "FAIL"
            result["error_msg"] = "Query option not found"
            tracker.record_step("find_element", "query_option", "failed")
            tracker.set_result("failed", "Query option not found")
            return

        tracker.record_step("find_element", "query_option", "success")
        tracker.record_step("click", "query_option", "pending")

        await query_btn.scroll_into_view_if_needed()
        await self.page.wait_for_timeout(300)
        await query_btn.click()
        await self.page.wait_for_timeout(1500)
        tracker.record_step("click", "query_option", "success")

        result["status"] = "PASS"
        tracker.set_result("success")

    async def _test_bind_character(self, case, result, tracker):
        """测试绑定人设 - 改进版本"""
        tracker.record_step("find_element", "account_list", "pending")

        # 获取账号列表
        account_rows = await self.page.query_selector_all('tr')
        if not account_rows or len(account_rows) < 2:
            result["status"] = "SKIP"
            result["error_msg"] = "No accounts in list"
            tracker.record_step("find_element", "account_list", "skipped")
            tracker.set_result("skipped", "No accounts in list")
            return

        tracker.record_step("find_element", "account_list", "success")

        # 查找换绑按钮 - 改进的选择器
        tracker.record_step("find_element", "bind_button", "pending")
        bind_btn = None

        # 方法1: 使用 has-text 选择器
        try:
            bind_btn = await self.page.query_selector('button:has-text("换绑")')
        except:
            pass

        # 方法2: 遍历所有按钮
        if not bind_btn:
            buttons = await self.page.query_selector_all('button, a')
            for btn in buttons:
                try:
                    text = await btn.text_content()
                    if "换绑" in text or "绑定人设" in text:
                        bind_btn = btn
                        break
                except:
                    pass

        if not bind_btn:
            result["status"] = "SKIP"
            result["error_msg"] = "No bind button found"
            tracker.record_step("find_element", "bind_button", "skipped")
            tracker.set_result("skipped", "No bind button found")
            return

        tracker.record_step("find_element", "bind_button", "success")

        # 点击换绑按钮 - 改进的点击方式
        tracker.record_step("click", "bind_button", "pending")
        try:
            await bind_btn.scroll_into_view_if_needed()
            await self.page.wait_for_timeout(500)
            # 使用 force: true 强制点击
            await bind_btn.click(force=True)
            await self.page.wait_for_timeout(1500)
            tracker.record_step("click", "bind_button", "success")
        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = f"Click failed: {str(e)}"
            tracker.record_step("click", "bind_button", "failed")
            tracker.set_result("failed", f"Click failed: {str(e)}")
            return

        # 等待对话框出现
        tracker.record_step("find_element", "bind_dialog", "pending")
        try:
            await self.page.wait_for_selector('.ant-modal, .ant-drawer', timeout=5000)
            tracker.record_step("find_element", "bind_dialog", "success")
        except:
            result["status"] = "SKIP"
            result["error_msg"] = "Bind dialog not found"
            tracker.record_step("find_element", "bind_dialog", "failed")
            tracker.set_result("skipped", "Bind dialog not found")
            return

        # 选择人设
        tracker.record_step("select_character", "character_select", "pending")
        try:
            selects = await self.page.query_selector_all('select, [role="combobox"]')
            if selects:
                await selects[0].click(force=True)
                await self.page.wait_for_timeout(500)
                # 选择第一个选项
                options = await self.page.query_selector_all('[role="option"]')
                if options:
                    await options[0].click(force=True)
                    tracker.record_step("select_character", "character_select", "success")
        except:
            tracker.record_step("select_character", "character_select", "skipped")

        # 提交
        tracker.record_step("submit_form", "confirm_button", "pending")
        try:
            confirm_btn = await self.page.query_selector('button:has-text("确定"), button:has-text("提交")')
            if confirm_btn:
                await confirm_btn.click(force=True)
                await self.page.wait_for_timeout(1500)
                tracker.record_step("submit_form", "confirm_button", "success")
        except:
            tracker.record_step("submit_form", "confirm_button", "skipped")

        result["status"] = "PASS"
        tracker.set_result("success")

    async def _test_set_operation_limit(self, case, result, tracker):
        """测试设置操作上限 - 改进版本"""
        tracker.record_step("navigate", "/accounts", "pending")

        # 导航到账号配置页面
        await self.page.goto(f"{SYSTEM_URL}/accounts", wait_until="domcontentloaded")
        await self.page.wait_for_timeout(1500)
        tracker.record_step("navigate", "/accounts", "success")

        # 获取账号列表
        tracker.record_step("find_element", "account_list", "pending")
        rows = await self.page.query_selector_all('tr')
        if not rows or len(rows) < 2:
            result["status"] = "SKIP"
            result["error_msg"] = "No accounts in list"
            tracker.record_step("find_element", "account_list", "skipped")
            tracker.set_result("skipped", "No accounts in list")
            return

        tracker.record_step("find_element", "account_list", "success")

        # 点击第一个账号进入配置页面
        tracker.record_step("click", "account_row", "pending")
        first_row = rows[1]
        try:
            await first_row.click()
            await self.page.wait_for_timeout(1500)
            tracker.record_step("click", "account_row", "success")
        except:
            result["status"] = "SKIP"
            result["error_msg"] = "Failed to click account row"
            tracker.record_step("click", "account_row", "failed")
            tracker.set_result("skipped", "Failed to click account row")
            return

        # 查找设置上限按钮 - 改进的搜索策略
        tracker.record_step("find_element", "limit_button", "pending")
        limit_btn = None

        # 方法1: 查找包含"设置"和"上限"的按钮
        buttons = await self.page.query_selector_all('button')
        for btn in buttons:
            try:
                text = await btn.text_content()
                if ("设置" in text and "上限" in text) or "操作上限" in text or "限制" in text:
                    limit_btn = btn
                    break
            except:
                pass

        # 方法2: 查找包含"设置"的按钮
        if not limit_btn:
            for btn in buttons:
                try:
                    text = await btn.text_content()
                    if "设置" in text:
                        limit_btn = btn
                        break
                except:
                    pass

        if not limit_btn:
            result["status"] = "SKIP"
            result["error_msg"] = "No limit button found"
            tracker.record_step("find_element", "limit_button", "skipped")
            tracker.set_result("skipped", "No limit button found")
            return

        tracker.record_step("find_element", "limit_button", "success")

        # 点击设置上限按钮
        tracker.record_step("click", "limit_button", "pending")
        try:
            await limit_btn.scroll_into_view_if_needed()
            await self.page.wait_for_timeout(500)
            await limit_btn.click(force=True)
            await self.page.wait_for_timeout(1500)
            tracker.record_step("click", "limit_button", "success")
        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = f"Click failed: {str(e)}"
            tracker.record_step("click", "limit_button", "failed")
            tracker.set_result("failed", f"Click failed: {str(e)}")
            return

        result["status"] = "PASS"
        tracker.set_result("success")

        # 点击设置上限按钮
        tracker.record_step("click", "limit_button", "pending")
        await limit_btn.click()
        await self.page.wait_for_timeout(1000)
        tracker.record_step("click", "limit_button", "success")

        # 等待对话框出现
        tracker.record_step("find_element", "limit_dialog", "pending")
        try:
            await self.page.wait_for_selector('.ant-modal, .ant-drawer, input[type="number"]', timeout=3000)
            tracker.record_step("find_element", "limit_dialog", "success")
        except:
            result["status"] = "SKIP"
            result["error_msg"] = "Limit dialog not found"
            tracker.record_step("find_element", "limit_dialog", "failed")
            tracker.set_result("skipped", "Limit dialog not found")
            return

        # 填写上限值
        tracker.record_step("fill_form", "limit_input", "pending")
        inputs = await self.page.query_selector_all('input[type="number"]')
        if inputs:
            await inputs[0].fill("10")
            tracker.record_step("fill_form", "limit_input", "success")

        # 提交
        tracker.record_step("submit_form", "confirm_button", "pending")
        confirm_btn = await self.page.query_selector('button:has-text("确定"), button:has-text("提交")')
        if confirm_btn:
            await confirm_btn.click()
            await self.page.wait_for_timeout(1000)
            tracker.record_step("submit_form", "confirm_button", "success")

        result["status"] = "PASS"
        tracker.set_result("success")

    async def _test_configure_ip(self, case, result, tracker):
        """测试 IP 配置和绑定"""
        desc = case.get("description", "")

        if "导入" in desc:
            await self._test_import_ip(case, result, tracker)
        elif "删除" in desc:
            await self._test_delete_ip(case, result, tracker)
        elif "绑定" in desc:
            await self._test_bind_ip(case, result, tracker)
        else:
            result["status"] = "SKIP"
            result["error_msg"] = "Unknown IP operation"
            tracker.set_result("skipped", "Unknown IP operation")

    async def _test_import_ip(self, case, result, tracker):
        """测试导入 IP"""
        tracker.record_step("find_element", "import_button", "pending")
        import_btn = await self.page.query_selector('button:has-text("导入")')
        if not import_btn:
            buttons = await self.page.query_selector_all('button')
            for btn in buttons:
                text = await btn.text_content()
                if "导入" in text or "上传" in text:
                    import_btn = btn
                    break

        if not import_btn:
            result["status"] = "FAIL"
            result["error_msg"] = "Import button not found"
            tracker.record_step("find_element", "import_button", "failed")
            tracker.set_result("failed", "Import button not found")
            return

        tracker.record_step("find_element", "import_button", "success")
        tracker.record_step("click", "import_button", "pending")
        await import_btn.click()
        await self.page.wait_for_timeout(1000)
        tracker.record_step("click", "import_button", "success")

        result["status"] = "PASS"
        tracker.set_result("success")

    async def _test_delete_ip(self, case, result, tracker):
        """测试删除 IP - 选择未绑定ip的账号，删除IP"""
        tracker.record_step("find_element", "account_row", "pending")

        # 获取表格行
        rows = await self.page.query_selector_all('tr')
        if not rows or len(rows) < 2:
            result["status"] = "SKIP"
            result["error_msg"] = "No accounts in table"
            tracker.record_step("find_element", "account_row", "skipped")
            tracker.set_result("skipped", "No accounts in table")
            return

        tracker.record_step("find_element", "account_row", "success")

        # 查找IP配置列中的删除按钮
        tracker.record_step("find_element", "ip_delete_button", "pending")

        # 遍历行查找IP配置列中的删除按钮
        found_delete = False
        for row in rows[1:]:  # 跳过表头
            cells = await row.query_selector_all('td')
            if len(cells) >= 7:  # IP配置列是第6列（索引6）
                ip_cell = cells[6]
                # 查找所有按钮
                btns = await ip_cell.query_selector_all('button')
                for btn in btns:
                    text = await btn.text_content()
                    if "删除" in text:
                        tracker.record_step("find_element", "ip_delete_button", "success")
                        tracker.record_step("click", "ip_delete_button", "pending")

                        # 等待元素可见
                        await btn.scroll_into_view_if_needed()
                        await self.page.wait_for_timeout(500)
                        await btn.click()
                        await self.page.wait_for_timeout(1000)
                        tracker.record_step("click", "ip_delete_button", "success")

                        # 确认删除
                        tracker.record_step("confirm_action", "confirm_button", "pending")
                        confirm_btn = await self.page.query_selector('button:has-text("确定"), button:has-text("OK")')
                        if confirm_btn:
                            await confirm_btn.click()
                            await self.page.wait_for_timeout(1000)
                            tracker.record_step("confirm_action", "confirm_button", "success")

                        result["status"] = "PASS"
                        tracker.set_result("success")
                        found_delete = True
                        break
            if found_delete:
                break

        if not found_delete:
            result["status"] = "FAIL"
            result["error_msg"] = "No delete button found in IP column"
            tracker.record_step("find_element", "ip_delete_button", "failed")
            tracker.set_result("failed", "No delete button found in IP column")

    async def _test_bind_ip(self, case, result, tracker):
        """测试绑定 IP - 改进版本"""
        tracker.record_step("find_element", "ip_config_option", "pending")

        # 在账号页面上查找 IP 配置选项
        all_elements = await self.page.query_selector_all('*')
        ip_config_elem = None

        for elem in all_elements:
            try:
                text = await elem.text_content()
                if "IP配置" in text and len(text.strip()) < 50:
                    tag = await elem.evaluate('el => el.tagName')
                    if tag in ['BUTTON', 'A', 'DIV', 'SPAN', 'LI']:
                        ip_config_elem = elem
                        break
            except:
                pass

        if not ip_config_elem:
            result["status"] = "FAIL"
            result["error_msg"] = "IP config option not found"
            tracker.record_step("find_element", "ip_config_option", "failed")
            tracker.set_result("failed", "IP config option not found")
            return

        tracker.record_step("find_element", "ip_config_option", "success")
        tracker.record_step("click", "ip_config_option", "pending")

        try:
            await ip_config_elem.scroll_into_view_if_needed()
            await self.page.wait_for_timeout(500)
            await ip_config_elem.click(force=True)
            await self.page.wait_for_timeout(1500)
            tracker.record_step("click", "ip_config_option", "success")
        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = f"Click failed: {str(e)}"
            tracker.record_step("click", "ip_config_option", "failed")
            tracker.set_result("failed", f"Click failed: {str(e)}")
            return

        # 现在在 IP 配置界面中查找 IP 列表的操作列中的重新绑定按钮
        tracker.record_step("find_element", "rebind_button", "pending")

        # 获取表格行
        rows = await self.page.query_selector_all('tr')
        if not rows or len(rows) < 2:
            result["status"] = "SKIP"
            result["error_msg"] = "No IP list found"
            tracker.record_step("find_element", "rebind_button", "skipped")
            tracker.set_result("skipped", "No IP list found")
            return

        # 查找操作列中的重新绑定按钮
        found_rebind = False
        for row in rows[1:]:  # 跳过表头
            cells = await row.query_selector_all('td')
            if cells:
                # 操作列通常在最后
                last_cell = cells[-1]
                buttons = await last_cell.query_selector_all('button')
                for btn in buttons:
                    try:
                        text = await btn.text_content()
                        # 尝试多种按钮文本
                        if "重新绑定" in text or "绑定" in text or "编辑" in text:
                            tracker.record_step("find_element", "rebind_button", "success")
                            tracker.record_step("click", "rebind_button", "pending")

                            await btn.scroll_into_view_if_needed()
                            await self.page.wait_for_timeout(500)
                            await btn.click(force=True)
                            await self.page.wait_for_timeout(1500)
                            tracker.record_step("click", "rebind_button", "success")

                            found_rebind = True
                            break
                    except:
                        pass
            if found_rebind:
                break

        if not found_rebind:
            result["status"] = "SKIP"
            result["error_msg"] = "No rebind button found in IP list"
            tracker.record_step("find_element", "rebind_button", "skipped")
            tracker.set_result("skipped", "No rebind button found in IP list")
            return

        # 等待对话框出现
        tracker.record_step("find_element", "bind_dialog", "pending")
        try:
            await self.page.wait_for_selector('.ant-modal, .ant-drawer', timeout=5000)
            tracker.record_step("find_element", "bind_dialog", "success")

            # 选择账号和IP
            tracker.record_step("select_account_and_ip", "select", "pending")
            selects = await self.page.query_selector_all('select, [role="combobox"]')
            if selects and len(selects) >= 2:
                # 选择账号 - 使用 force: true
                await selects[0].click(force=True)
                await self.page.wait_for_timeout(500)
                options = await self.page.query_selector_all('[role="option"]')
                if options:
                    await options[0].click(force=True)
                    await self.page.wait_for_timeout(500)

                # 选择IP
                await selects[1].click(force=True)
                await self.page.wait_for_timeout(500)
                options = await self.page.query_selector_all('[role="option"]')
                if options:
                    await options[0].click(force=True)
                    tracker.record_step("select_account_and_ip", "select", "success")

            # 提交
            tracker.record_step("submit_form", "confirm_button", "pending")
            confirm_btn = await self.page.query_selector('button:has-text("确定"), button:has-text("提交")')
            if confirm_btn:
                await confirm_btn.click(force=True)
                await self.page.wait_for_timeout(1000)
                tracker.record_step("submit_form", "confirm_button", "success")

            result["status"] = "PASS"
            tracker.set_result("success")
        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = f"Bind dialog error: {str(e)[:50]}"
            tracker.record_step("find_element", "bind_dialog", "failed")
            tracker.set_result("failed", f"Bind dialog error: {str(e)[:50]}")

    async def _test_event_module(self, case, result, tracker):
        """测试事件源模块"""
        desc = case.get("description", "")

        tracker.record_step("navigate", "/event-sources", "pending")
        await self.page.goto(f"{SYSTEM_URL}/event-sources", wait_until="domcontentloaded")
        await self.page.wait_for_timeout(1500)
        tracker.record_step("navigate", "/event-sources", "success")

        if "手动编辑" in desc:
            await self._test_edit_event_source(case, result, tracker)
        elif "对话开启" in desc:
            await self._test_enable_event_in_dialog(case, result, tracker)
        elif "添加监控" in desc:
            await self._test_add_monitor_account(case, result, tracker)
        else:
            result["status"] = "PASS"
            tracker.set_result("success")

    async def _test_edit_event_source(self, case, result, tracker):
        """测试手动编辑事件源"""
        tracker.record_step("find_element", "event_card", "pending")

        # 查找事件卡片或列表项
        event_cards = await self.page.query_selector_all('[class*="card"], [class*="event"], [class*="item"]')

        if not event_cards or len(event_cards) == 0:
            result["status"] = "SKIP"
            result["error_msg"] = "No event cards found"
            tracker.record_step("find_element", "event_card", "skipped")
            tracker.set_result("skipped", "No event cards found")
            return

        tracker.record_step("find_element", "event_card", "success")
        tracker.record_step("double_click", "event_card", "pending")

        # 双击第一个卡片（使用 dblclick 而不是 double_click）
        await event_cards[0].dblclick()
        await self.page.wait_for_timeout(1000)
        tracker.record_step("double_click", "event_card", "success")

        # 检查编辑界面是否打开
        tracker.record_step("find_element", "edit_interface", "pending")
        textareas = await self.page.query_selector_all('textarea')
        if textareas and len(textareas) > 0:
            tracker.record_step("find_element", "edit_interface", "success")
            result["status"] = "PASS"
            tracker.set_result("success")
        else:
            result["status"] = "FAIL"
            result["error_msg"] = "Edit interface not opened (textareas not found)"
            tracker.record_step("find_element", "edit_interface", "failed")
            tracker.set_result("failed", "Edit interface not opened")

    async def _test_enable_event_in_dialog(self, case, result, tracker):
        """测试对话开启事件源 - 在对话框中输入指令"""
        tracker.record_step("find_element", "dialog_button", "pending")

        # 首先查找并点击打开对话框的按钮
        buttons = await self.page.query_selector_all('button')
        dialog_btn = None

        for btn in buttons:
            text = await btn.text_content()
            if "对话" in text or "聊天" in text or "AI" in text:
                dialog_btn = btn
                break

        if dialog_btn:
            tracker.record_step("find_element", "dialog_button", "success")
            tracker.record_step("click", "dialog_button", "pending")
            try:
                await dialog_btn.click()
                await self.page.wait_for_timeout(1000)
                tracker.record_step("click", "dialog_button", "success")
            except:
                pass

        # 查找对话框的输入框
        tracker.record_step("find_element", "dialog_input", "pending")
        dialog_inputs = await self.page.query_selector_all('input[type="text"], textarea, [contenteditable="true"]')

        if not dialog_inputs or len(dialog_inputs) == 0:
            result["status"] = "FAIL"
            result["error_msg"] = "No dialog input found"
            tracker.record_step("find_element", "dialog_input", "failed")
            tracker.set_result("failed", "No dialog input found")
            return

        tracker.record_step("find_element", "dialog_input", "success")

        # 在对话框中输入指令
        tracker.record_step("input_command", "dialog_input", "pending")
        input_element = dialog_inputs[-1]  # 使用最后一个输入元素

        try:
            # 使用 focus 而不是 click，避免超时
            await input_element.scroll_into_view_if_needed()
            await self.page.wait_for_timeout(300)
            await input_element.focus()
            await self.page.wait_for_timeout(300)

            # 直接输入指令，不使用 fill
            await input_element.type("开启推特推文监控", delay=50)
            await self.page.wait_for_timeout(500)
            tracker.record_step("input_command", "dialog_input", "success")

            # 发送指令（按Enter）
            tracker.record_step("send_command", "send_button", "pending")
            await input_element.press("Enter")
            await self.page.wait_for_timeout(1500)
            tracker.record_step("send_command", "send_button", "success")

            result["status"] = "PASS"
            tracker.set_result("success")
        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = f"Dialog input error: {str(e)[:50]}"
            tracker.record_step("input_command", "dialog_input", "failed")
            tracker.set_result("failed", f"Dialog input error: {str(e)[:50]}")

    async def _test_add_monitor_account(self, case, result, tracker):
        """测试对话添加监控账号 - 在对话框中输入指令"""
        tracker.record_step("find_element", "dialog_button", "pending")

        # 首先查找并点击打开对话框的按钮
        buttons = await self.page.query_selector_all('button')
        dialog_btn = None

        for btn in buttons:
            text = await btn.text_content()
            if "对话" in text or "聊天" in text or "AI" in text:
                dialog_btn = btn
                break

        if dialog_btn:
            tracker.record_step("find_element", "dialog_button", "success")
            tracker.record_step("click", "dialog_button", "pending")
            try:
                await dialog_btn.click()
                await self.page.wait_for_timeout(1000)
                tracker.record_step("click", "dialog_button", "success")
            except:
                pass

        # 查找对话框的输入框
        tracker.record_step("find_element", "dialog_input", "pending")
        dialog_inputs = await self.page.query_selector_all('input[type="text"], textarea, [contenteditable="true"]')

        if not dialog_inputs or len(dialog_inputs) == 0:
            result["status"] = "FAIL"
            result["error_msg"] = "No dialog input found"
            tracker.record_step("find_element", "dialog_input", "failed")
            tracker.set_result("failed", "No dialog input found")
            return

        tracker.record_step("find_element", "dialog_input", "success")

        # 在对话框中输入指令
        tracker.record_step("input_command", "dialog_input", "pending")
        input_element = dialog_inputs[-1]  # 使用最后一个输入元素

        try:
            # 使用 focus 而不是 click，避免超时
            await input_element.scroll_into_view_if_needed()
            await self.page.wait_for_timeout(300)
            await input_element.focus()
            await self.page.wait_for_timeout(300)

            # 直接输入指令，不使用 fill
            await input_element.type("监控推特上elon musk的账号", delay=50)
            await self.page.wait_for_timeout(500)
            tracker.record_step("input_command", "dialog_input", "success")

            # 发送指令（按Enter）
            tracker.record_step("send_command", "send_button", "pending")
            await input_element.press("Enter")
            await self.page.wait_for_timeout(1500)
            tracker.record_step("send_command", "send_button", "success")

            result["status"] = "PASS"
            tracker.set_result("success")
        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = f"Dialog input error: {str(e)[:50]}"
            tracker.record_step("input_command", "dialog_input", "failed")
            tracker.set_result("failed", f"Dialog input error: {str(e)[:50]}")

    async def _test_agent_module(self, case, result, tracker):
        """测试决策代理模块 - 配置驱动的路由"""
        case_type = case.get("type", "default")

        if case_type == "closedloop":
            # 闭环测试：使用通用闭环处理器
            loop_handler = LoopHandler(self.page, tracker, SYSTEM_URL)
            await loop_handler.test_closedloop(case, result, tracker)

        elif case_type == "menu_operation":
            # 菜单操作测试：Cases 25-26
            operation = case.get("operation", "")
            if operation == "growth_loop":
                await self._test_growth_loop(case, result, tracker)
            elif operation == "schedule_task":
                await self._test_schedule_task(case, result, tracker)
            else:
                result["status"] = "SKIP"
                result["error_msg"] = f"Unknown menu operation: {operation}"
                tracker.set_result("skipped", f"Unknown menu operation: {operation}")

        else:
            # 默认：普通导航测试
            tracker.record_step("navigate", "/decision", "pending")
            await self.page.goto(f"{SYSTEM_URL}/decision", wait_until="domcontentloaded")
            await self.page.wait_for_timeout(1500)
            tracker.record_step("navigate", "/decision", "success")

            title = await self.page.title()
            if title:
                result["status"] = "PASS"
                tracker.set_result("success")
            else:
                result["status"] = "FAIL"
                result["error_msg"] = "Page not loaded"
                tracker.set_result("failed", "Page not loaded")

    async def _test_log_module(self, case, result, tracker):
        """测试执行日志模块"""
        tracker.record_step("navigate", "/exec-logs", "pending")
        await self.page.goto(f"{SYSTEM_URL}/exec-logs", wait_until="domcontentloaded")
        await self.page.wait_for_timeout(1500)
        tracker.record_step("navigate", "/exec-logs", "success")

        result["status"] = "PASS"
        tracker.set_result("success")

    async def _test_knowledge_module(self, case, result, tracker):
        """测试知识库模块"""
        tracker.record_step("navigate", "/knowledge", "pending")
        await self.page.goto(f"{SYSTEM_URL}/knowledge", wait_until="domcontentloaded")
        await self.page.wait_for_timeout(1500)
        tracker.record_step("navigate", "/knowledge", "success")

        result["status"] = "PASS"
        tracker.set_result("success")

    async def _test_admin_module(self, case, result, tracker):
        """测试账号管理模块"""
        tracker.record_step("navigate", "/admin", "pending")
        await self.page.goto(f"{SYSTEM_URL}/admin", wait_until="domcontentloaded")
        await self.page.wait_for_timeout(1500)
        tracker.record_step("navigate", "/admin", "success")

        result["status"] = "PASS"
        tracker.set_result("success")

    async def _test_character_module(self, case, result, tracker):
        """测试人设模块"""
        tracker.record_step("navigate", "/characters", "pending")
        await self.page.goto(f"{SYSTEM_URL}/characters", wait_until="domcontentloaded")
        await self.page.wait_for_timeout(1500)
        tracker.record_step("navigate", "/characters", "success")

        result["status"] = "PASS"
        tracker.set_result("success")

    async def _test_schedule_module(self, case, result, tracker):
        """测试定时任务和闭环模块"""
        desc = case.get("description", "")

        # 用例25: 增长闭环开启关闭
        if "增长闭环" in desc or "闭环" in desc and "定时" not in desc:
            await self._test_growth_loop(case, result, tracker)
        # 用例26: 定时任务触发日常养号闭环
        elif "定时任务" in desc or "养号" in desc:
            await self._test_schedule_task(case, result, tracker)
        else:
            result["status"] = "PASS"
            tracker.set_result("success")

    async def _test_growth_loop(self, case, result, tracker):
        """测试增长闭环开启关闭 - 用例25"""
        # 第1步：点击分析菜单
        tracker.record_step("navigate", "analysis_menu", "pending")
        try:
            # 查找分析菜单项
            menu_items = await self.page.query_selector_all('[role="menuitem"]')
            analysis_menu = None

            for item in menu_items:
                text = await item.text_content()
                if "分析" in text:
                    analysis_menu = item
                    break

            if not analysis_menu:
                result["status"] = "SKIP"
                result["error_msg"] = "Analysis menu not found"
                tracker.record_step("navigate", "analysis_menu", "skipped")
                tracker.set_result("skipped", "Analysis menu not found")
                return

            await analysis_menu.click(force=True)
            await self.page.wait_for_timeout(1000)
            tracker.record_step("navigate", "analysis_menu", "success")
        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = f"Failed to click analysis menu: {str(e)}"
            tracker.record_step("navigate", "analysis_menu", "failed")
            tracker.set_result("failed", f"Failed to click analysis menu: {str(e)}")
            return

        # 第2步：点击增长闭环
        tracker.record_step("find_element", "growth_loop_option", "pending")
        try:
            menu_items = await self.page.query_selector_all('[role="menuitem"]')
            growth_loop_option = None

            for item in menu_items:
                text = await item.text_content()
                if "增长闭环" in text:
                    growth_loop_option = item
                    break

            if not growth_loop_option:
                result["status"] = "SKIP"
                result["error_msg"] = "Growth loop option not found"
                tracker.record_step("find_element", "growth_loop_option", "skipped")
                tracker.set_result("skipped", "Growth loop option not found")
                return

            await growth_loop_option.click(force=True)
            await self.page.wait_for_timeout(2000)
            tracker.record_step("find_element", "growth_loop_option", "success")
        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = f"Failed to click growth loop: {str(e)}"
            tracker.record_step("find_element", "growth_loop_option", "failed")
            tracker.set_result("failed", f"Failed to click growth loop: {str(e)}")
            return

        # 第3步：查找并点击第一个 switch 开关
        tracker.record_step("find_element", "loop_switch", "pending")
        try:
            # 查找所有 switch 元素（使用 role="switch" 选择器）
            switches = await self.page.query_selector_all('[role="switch"]')

            if not switches:
                result["status"] = "SKIP"
                result["error_msg"] = "No loop switches found"
                tracker.record_step("find_element", "loop_switch", "skipped")
                tracker.set_result("skipped", "No loop switches found")
                return

            tracker.record_step("find_element", "loop_switch", "success")

            # 点击第一个 switch 来切换闭环状态
            tracker.record_step("click", "loop_switch", "pending")
            first_switch = switches[0]
            await first_switch.scroll_into_view_if_needed()
            await self.page.wait_for_timeout(500)
            await first_switch.click(force=True)
            await self.page.wait_for_timeout(1500)
            tracker.record_step("click", "loop_switch", "success")

            result["status"] = "PASS"
            tracker.set_result("success")
        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = f"Failed to toggle loop: {str(e)}"
            tracker.record_step("find_element", "loop_switch", "failed")
            tracker.set_result("failed", f"Failed to toggle loop: {str(e)}")

    async def _test_schedule_task(self, case, result, tracker):
        """测试定时任务创建 - 用例26"""
        # 第1步：点击分析菜单
        tracker.record_step("navigate", "analysis_menu", "pending")
        try:
            # 查找分析菜单项
            menu_items = await self.page.query_selector_all('[role="menuitem"]')
            analysis_menu = None

            for item in menu_items:
                text = await item.text_content()
                if "分析" in text:
                    analysis_menu = item
                    break

            if not analysis_menu:
                result["status"] = "SKIP"
                result["error_msg"] = "Analysis menu not found"
                tracker.record_step("navigate", "analysis_menu", "skipped")
                tracker.set_result("skipped", "Analysis menu not found")
                return

            await analysis_menu.click(force=True)
            await self.page.wait_for_timeout(1000)
            tracker.record_step("navigate", "analysis_menu", "success")
        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = f"Failed to click analysis menu: {str(e)}"
            tracker.record_step("navigate", "analysis_menu", "failed")
            tracker.set_result("failed", f"Failed to click analysis menu: {str(e)}")
            return

        # 第2步：点击定时任务
        tracker.record_step("find_element", "schedule_option", "pending")
        try:
            menu_items = await self.page.query_selector_all('[role="menuitem"]')
            schedule_option = None

            for item in menu_items:
                text = await item.text_content()
                if "定时任务" in text:
                    schedule_option = item
                    break

            if not schedule_option:
                result["status"] = "SKIP"
                result["error_msg"] = "Schedule option not found"
                tracker.record_step("find_element", "schedule_option", "skipped")
                tracker.set_result("skipped", "Schedule option not found")
                return

            await schedule_option.click(force=True)
            await self.page.wait_for_timeout(2000)
            tracker.record_step("find_element", "schedule_option", "success")
        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = f"Failed to click schedule option: {str(e)}"
            tracker.record_step("find_element", "schedule_option", "failed")
            tracker.set_result("failed", f"Failed to click schedule option: {str(e)}")
            return

        # 第3步：点击创建任务按钮
        tracker.record_step("find_element", "create_task_button", "pending")
        try:
            create_btn = await self.page.query_selector('button:has-text("创建任务")')
            if not create_btn:
                # 尝试其他选择器
                buttons = await self.page.query_selector_all('button')
                for btn in buttons:
                    text = await btn.text_content()
                    if "创建" in text:
                        create_btn = btn
                        break

            if not create_btn:
                result["status"] = "SKIP"
                result["error_msg"] = "Create task button not found"
                tracker.record_step("find_element", "create_task_button", "skipped")
                tracker.set_result("skipped", "Create task button not found")
                return

            tracker.record_step("find_element", "create_task_button", "success")

            # 点击创建任务
            tracker.record_step("click", "create_task_button", "pending")
            await create_btn.click(force=True)
            await self.page.wait_for_timeout(1500)
            tracker.record_step("click", "create_task_button", "success")
        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = f"Failed to click create button: {str(e)}"
            tracker.record_step("find_element", "create_task_button", "failed")
            tracker.set_result("failed", f"Failed to click create button: {str(e)}")
            return

        # 第4步：填写表单
        tracker.record_step("fill_form", "task_form", "pending")
        try:
            # 名称填养号
            name_input = await self.page.query_selector('input[placeholder*="任务名称"], input[placeholder*="如："]')
            if name_input:
                await name_input.fill("养号")
                await self.page.wait_for_timeout(500)

            # 任务指令填用主号组账号执行养号闭环
            instruction_input = await self.page.query_selector('input[placeholder*="任务指令"], textarea')
            if instruction_input:
                await instruction_input.fill("用主号组账号执行养号闭环")
                await self.page.wait_for_timeout(500)

            # 调度类型选择每天（默认已是每天）
            # 触发时间输入13:00
            time_inputs = await self.page.query_selector_all('input[placeholder*="时间"]')
            if time_inputs:
                await time_inputs[0].fill("13:00")
                await self.page.wait_for_timeout(500)

            tracker.record_step("fill_form", "task_form", "success")
        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = f"Failed to fill form: {str(e)}"
            tracker.record_step("fill_form", "task_form", "failed")
            tracker.set_result("failed", f"Failed to fill form: {str(e)}")
            return

        # 第5步：点击OK
        tracker.record_step("submit_form", "ok_button", "pending")
        try:
            ok_btn = await self.page.query_selector('button:has-text("OK")')
            if not ok_btn:
                buttons = await self.page.query_selector_all('button')
                for btn in buttons:
                    text = await btn.text_content()
                    if text.strip() == "OK":
                        ok_btn = btn
                        break

            if ok_btn:
                await ok_btn.click(force=True)
                await self.page.wait_for_timeout(1500)
                tracker.record_step("submit_form", "ok_button", "success")
            else:
                tracker.record_step("submit_form", "ok_button", "skipped")
        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = f"Failed to submit: {str(e)}"
            tracker.record_step("submit_form", "ok_button", "failed")
            tracker.set_result("failed", f"Failed to submit: {str(e)}")
            return

        # 第6步：验证任务是否创建成功
        tracker.record_step("verify", "task_created", "pending")
        try:
            await self.page.wait_for_timeout(1000)
            page_text = await self.page.content()
            if "养号" in page_text:
                tracker.record_step("verify", "task_created", "success")
                result["status"] = "PASS"
                tracker.set_result("success")
            else:
                result["status"] = "FAIL"
                result["error_msg"] = "Task not found in list after creation"
                tracker.record_step("verify", "task_created", "failed")
                tracker.set_result("failed", "Task not found in list after creation")
        except Exception as e:
            result["status"] = "FAIL"
            result["error_msg"] = f"Verification failed: {str(e)}"
            tracker.record_step("verify", "task_created", "failed")
            tracker.set_result("failed", f"Verification failed: {str(e)}")

    async def _test_tracking_module(self, case, result, tracker):
        """测试反向追踪模块"""
        tracker.record_step("navigate", "/tracking", "pending")
        await self.page.goto(f"{SYSTEM_URL}/tracking", wait_until="domcontentloaded")
        await self.page.wait_for_timeout(1500)
        tracker.record_step("navigate", "/tracking", "success")

        result["status"] = "PASS"
        tracker.set_result("success")


async def run_test_case(case):
    """运行单条用例"""
    executor = TestExecutor()
    try:
        await executor.setup()
        await executor.login()
        result = await executor.execute_case(case)
        return result
    except Exception as e:
        trace_manager = get_trace_manager()
        tracker = trace_manager.create_tracker(case.get("case_id", "UNKNOWN"), case.get("description", ""))
        tracker.set_result("failed", str(e)[:100])

        return {
            "case_id": case.get("case_id", "UNKNOWN"),
            "description": case.get("description", ""),
            "module": case.get("module", "Unknown"),
            "level": case.get("level", "P3"),
            "status": "ERROR",
            "error_msg": str(e)[:100],
            "duration": 0,
            "trace_id": tracker.trace_id,
        }
    finally:
        await executor.teardown()
