#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量执行器 - 依次执行闭环，工作流内部检测完成
"""
import asyncio
import sys
import io
from pathlib import Path
from datetime import datetime

# 修复编码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from executor.runner import TestExecutor
from trace.tracker import get_trace_manager
from loop_workflow.loop_monitor import LoopMonitor
from loop_workflow.loop_reporter import LoopReporter
from config import SYSTEM_URL, LOGIN_USERNAME, LOGIN_PASSWORD


class BatchExecutor:
    """批量执行器 - 依次执行所有闭环"""

    def __init__(self):
        self.executor = None
        self.results = []
        self.start_time = None

    async def run(self, loops):
        """
        执行所有闭环

        Args:
            loops: 闭环列表 [{'case_id': 1, 'name': '...', 'instruction': '...'}, ...]

        Returns:
            results: 执行结果列表
        """
        self.start_time = datetime.now()
        self.results = []

        print("\n" + "=" * 60)
        print("🚀 批量闭环测试")
        print("=" * 60)
        print(f"总数：{len(loops)} 个闭环")
        print("=" * 60)

        # 启动执行器
        self.executor = TestExecutor()
        await self.executor.setup()
        await self.executor.login()

        try:
            # 依次执行每个闭环
            for i, loop in enumerate(loops, 1):
                print(f"\n【{i}/{len(loops)}】执行: {loop['name']}")
                print("-" * 60)

                result = await self._run_single_loop(loop)
                self.results.append(result)

                # 显示结果
                status_icon = "✅" if result['status'] == 'success' else "❌" if result['status'] == 'failed' else "⚠️"
                print(f"{status_icon} 结果: {result['status']}")
                print(f"   耗时: {result['elapsed']}s")

                # 等待后开始下一个
                if i < len(loops):
                    print(f"\n⏳ 等待 5 秒后开始下一个闭环...")
                    await asyncio.sleep(5)

        finally:
            # 关闭执行器
            await self.executor.teardown()

        return self.results

    async def _run_single_loop(self, loop):
        """
        执行单个闭环

        工作流内部已经：
        ✅ 监控对话框内容
        ✅ 检测完成信号
        ✅ 识别到信号就返回
        """
        case_id = loop['case_id']
        case_name = loop['name']
        instruction = loop['instruction']

        # 创建追踪器
        trace_manager = get_trace_manager()
        tracker = trace_manager.create_tracker(case_id, case_name)

        result = {
            'case_id': case_id,
            'name': case_name,
            'instruction': instruction,
            'status': 'pending',
            'elapsed': 0,
            'error_msg': '',
            'trace_id': tracker.trace_id,
        }

        try:
            # 【第1阶段】输入指令（后台执行）
            print("[步骤1] 输入指令...")
            tracker.record_step("navigate", "/decision", "pending")
            await self.executor.page.goto(f"{SYSTEM_URL}/decision", wait_until="domcontentloaded")
            await self.executor.page.wait_for_timeout(2000)
            tracker.record_step("navigate", "/decision", "success")

            # 查找并点击第一个决策对话
            tracker.record_step("find_element", "decision_item", "pending")
            decision_items = await self.executor.page.query_selector_all('[class*="decision"], [class*="item"], tr, li')

            if not decision_items or len(decision_items) == 0:
                raise Exception("No decision items found")

            tracker.record_step("find_element", "decision_item", "success")
            tracker.record_step("click", "decision_item", "pending")
            await decision_items[0].click()
            await self.executor.page.wait_for_timeout(2000)
            tracker.record_step("click", "decision_item", "success")

            # 查找并点击"新建对话"按钮
            tracker.record_step("find_element", "create_dialog_button", "pending")
            buttons = await self.executor.page.query_selector_all('button')
            create_dialog_btn = None

            for btn in buttons:
                text = await btn.text_content()
                if "新建对话" in text or "新建" in text:
                    create_dialog_btn = btn
                    break

            if not create_dialog_btn:
                raise Exception("Create dialog button not found")

            tracker.record_step("find_element", "create_dialog_button", "success")
            tracker.record_step("click", "create_dialog_button", "pending")
            await create_dialog_btn.click()
            await self.executor.page.wait_for_timeout(2000)
            tracker.record_step("click", "create_dialog_button", "success")

            # 等待对话框出现
            tracker.record_step("wait_for_dialog", "dialog_load", "pending")
            try:
                await self.executor.page.wait_for_selector('input[type="text"], textarea, [contenteditable="true"]', timeout=5000)
                tracker.record_step("wait_for_dialog", "dialog_load", "success")
            except:
                tracker.record_step("wait_for_dialog", "dialog_load", "skipped")
                pass

            # 查找对话框的输入框
            tracker.record_step("find_element", "chat_input", "pending")
            dialog_inputs = await self.executor.page.query_selector_all('input[type="text"], textarea, [contenteditable="true"]')

            if not dialog_inputs or len(dialog_inputs) == 0:
                raise Exception("Chat input not found")

            tracker.record_step("find_element", "chat_input", "success")

            # 使用最后一个输入元素
            chat_input = dialog_inputs[-1]

            # 输入指令
            print("[步骤2] 输入指令...")
            tracker.record_step("input_instruction", "instruction", "pending")

            await chat_input.scroll_into_view_if_needed()
            await self.executor.page.wait_for_timeout(300)
            await chat_input.focus()
            await self.executor.page.wait_for_timeout(300)

            await chat_input.type(instruction, delay=50)
            await self.executor.page.wait_for_timeout(500)
            tracker.record_step("input_instruction", "instruction", "success", {"instruction": instruction})

            # 发送指令
            print("[步骤3] 发送指令...")
            tracker.record_step("send_instruction", "send_button", "pending")
            await chat_input.press("Enter")
            await self.executor.page.wait_for_timeout(1500)
            tracker.record_step("send_instruction", "send_button", "success")

            print("✓ 指令已发送")

            # 【第2阶段】实时监控（工作流内部检测完成）
            print("[步骤4] 实时监控对话框内容...")

            # 打开新的可见浏览器窗口用于监控
            from playwright.async_api import async_playwright

            monitor_playwright = await async_playwright().start()
            monitor_browser = await monitor_playwright.chromium.launch(headless=False)
            monitor_page = await monitor_browser.new_page()
            monitor_page.set_default_timeout(30000)

            # 监控浏览器登录
            print("[步骤5] 监控浏览器登录...")
            await monitor_page.goto(f"{SYSTEM_URL}/overview", wait_until="domcontentloaded")
            try:
                await monitor_page.wait_for_selector('input[type="text"]', timeout=5000)
                await monitor_page.fill('input[type="text"]', LOGIN_USERNAME)
                await monitor_page.fill('input[type="password"]', LOGIN_PASSWORD)
                login_btn = await monitor_page.query_selector('button')
                if login_btn:
                    await login_btn.click()
                await monitor_page.wait_for_url("**/overview", timeout=10000)
                print("✓ 监控浏览器已登录")
            except:
                print("✓ 监控浏览器已登录（或无需登录）")

            try:
                # 创建监控器
                monitor = LoopMonitor(SYSTEM_URL)
                success, content, screenshot_path, elapsed, message = await monitor.start_monitoring(
                    monitor_page,
                    check_interval=300,  # 5分钟
                    max_wait=18000,  # 5小时
                    instruction=instruction
                )

                result['status'] = 'success' if success else 'failed'
                result['elapsed'] = elapsed
                result['error_msg'] = '' if success else message
                result['check_count'] = monitor.check_count
                result['message'] = message
                tracker.set_result('success' if success else 'failed')

            finally:
                # 关闭监控浏览器
                await monitor_page.close()
                await monitor_browser.close()
                await monitor_playwright.stop()

        except Exception as e:
            result['status'] = 'error'
            result['error_msg'] = str(e)[:100]
            tracker.set_result('failed', str(e)[:100])
            print(f"❌ 错误: {str(e)}")

        finally:
            # 保存追踪日志
            trace_manager = get_trace_manager()
            trace_manager.save_all()

        return result
