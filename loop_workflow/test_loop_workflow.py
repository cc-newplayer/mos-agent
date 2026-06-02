#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闭环测试工作流 - 通用模板
用法：python test_loop_workflow.py <case_id> <case_name> <instruction>
例如：python test_loop_workflow.py 1 "KOL跟评闭环" "用一个引流号对@elonmusk最新的一篇推文执行KOL跟评闭环"
"""
import asyncio
import sys
import io
from pathlib import Path

# 修复编码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from executor.runner import TestExecutor
from trace.tracker import get_trace_manager
from loop_monitor import LoopMonitor
from loop_reporter import LoopReporter
from config import SYSTEM_URL, LOGIN_USERNAME, LOGIN_PASSWORD


async def main():
    # 解析命令行参数
    if len(sys.argv) < 4:
        print("用法: python test_loop_workflow.py <case_id> <case_name> <instruction>")
        print("例如: python test_loop_workflow.py 1 'KOL跟评闭环' '用一个引流号对@elonmusk最新的一篇推文执行KOL跟评闭环'")
        sys.exit(1)

    case_id = sys.argv[1]
    case_name = sys.argv[2]
    instruction = sys.argv[3]

    print("=" * 60)
    print("🚀 闭环测试工作流")
    print("=" * 60)
    print(f"用例ID: {case_id}")
    print(f"用例名称: {case_name}")
    print(f"指令: {instruction}")
    print("=" * 60)

    # 创建用例
    case = {
        "case_id": case_id,
        "description": case_name,
        "module": "决策对话",
        "level": "P1",
        "type": "closedloop",
        "instruction": instruction,
    }

    # 启动执行器
    executor = TestExecutor()
    await executor.setup()
    await executor.login()

    # 创建追踪器
    trace_manager = get_trace_manager()
    tracker = trace_manager.create_tracker(case_id, case_name)

    result = {
        "case_id": case_id,
        "description": case_name,
        "module": "决策对话",
        "level": "P1",
        "status": "PENDING",
        "error_msg": "",
        "duration": 0,
        "trace_id": tracker.trace_id,
    }

    try:
        # 【第1阶段】输入指令（后台执行）
        print("\n【第1阶段】输入指令（后台执行）")
        print("-" * 60)

        # 导航到决策对话页面
        print("[步骤1] 导航到决策对话页面...")
        tracker.record_step("navigate", "/decision", "pending")
        await executor.page.goto(f"{SYSTEM_URL}/decision", wait_until="domcontentloaded")
        await executor.page.wait_for_timeout(2000)
        tracker.record_step("navigate", "/decision", "success")
        print("✓ 已导航到决策对话页面")

        # 查找并点击第一个决策对话
        print("[步骤2] 查找并点击决策对话...")
        tracker.record_step("find_element", "decision_item", "pending")
        decision_items = await executor.page.query_selector_all('[class*="decision"], [class*="item"], tr, li')

        if not decision_items or len(decision_items) == 0:
            raise Exception("No decision items found")

        tracker.record_step("find_element", "decision_item", "success")
        tracker.record_step("click", "decision_item", "pending")
        await decision_items[0].click()
        await executor.page.wait_for_timeout(2000)
        tracker.record_step("click", "decision_item", "success")
        print("✓ 已点击决策对话")

        # 查找并点击"新建对话"按钮
        print("[步骤3] 查找并点击'新建对话'按钮...")
        tracker.record_step("find_element", "create_dialog_button", "pending")
        buttons = await executor.page.query_selector_all('button')
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
        await executor.page.wait_for_timeout(2000)
        tracker.record_step("click", "create_dialog_button", "success")
        print("✓ 已点击'新建对话'按钮")

        # 等待对话框出现
        print("[步骤4] 等待对话框出现...")
        tracker.record_step("wait_for_dialog", "dialog_load", "pending")
        try:
            await executor.page.wait_for_selector('input[type="text"], textarea, [contenteditable="true"]', timeout=5000)
            tracker.record_step("wait_for_dialog", "dialog_load", "success")
        except:
            tracker.record_step("wait_for_dialog", "dialog_load", "skipped")
            pass
        print("✓ 对话框已出现")

        # 查找对话框的输入框
        print("[步骤5] 查找对话框输入框...")
        tracker.record_step("find_element", "chat_input", "pending")
        dialog_inputs = await executor.page.query_selector_all('input[type="text"], textarea, [contenteditable="true"]')

        if not dialog_inputs or len(dialog_inputs) == 0:
            raise Exception("Chat input not found")

        tracker.record_step("find_element", "chat_input", "success")
        print("✓ 已找到输入框")

        # 使用最后一个输入元素（对话框输入框）
        chat_input = dialog_inputs[-1]

        # 输入指令
        print("[步骤6] 输入指令...")
        tracker.record_step("input_instruction", "instruction", "pending")

        await chat_input.scroll_into_view_if_needed()
        await executor.page.wait_for_timeout(300)
        await chat_input.focus()
        await executor.page.wait_for_timeout(300)

        await chat_input.type(instruction, delay=50)
        await executor.page.wait_for_timeout(500)
        tracker.record_step("input_instruction", "instruction", "success", {"instruction": instruction})
        print(f"✓ 已输入指令")

        # 发送指令（按Enter）
        print("[步骤7] 发送指令...")
        tracker.record_step("send_instruction", "send_button", "pending")
        await chat_input.press("Enter")
        await executor.page.wait_for_timeout(1500)
        tracker.record_step("send_instruction", "send_button", "success")
        print("✓ 已发送指令")

        print("\n✅ 指令已发送！")

        # 【第2阶段】实时监控（浏览器窗口可见）
        print("\n【第2阶段】实时监控对话框内容")
        print("-" * 60)

        # 打开新的可见浏览器窗口用于监控
        print("📺 打开监控浏览器窗口...")
        from playwright.async_api import async_playwright

        monitor_playwright = await async_playwright().start()
        monitor_browser = await monitor_playwright.chromium.launch(headless=False)
        monitor_page = await monitor_browser.new_page()
        monitor_page.set_default_timeout(30000)

        try:
            # 创建监控器
            monitor = LoopMonitor(SYSTEM_URL)
            success, content, screenshot_path, elapsed, message = await monitor.start_monitoring(
                monitor_page,
                check_interval=300,  # 5分钟
                max_wait=18000,  # 5小时
                instruction=instruction
            )

            # 【第3阶段】生成报告
            print("\n【第3阶段】生成报告")
            print("-" * 60)

            reporter = LoopReporter(case_id, case_name, instruction)
            report = reporter.generate_report(
                status="success" if success else "failed",
                elapsed_time=elapsed,
                content=content,
                screenshot_path=screenshot_path,
                check_count=monitor.check_count
            )

            reporter.print_report(report)

            # 推送到飞书
            print("\n【第4阶段】推送报告到飞书")
            print("-" * 60)
            reporter.send_to_feishu(report)

            result["status"] = "PASS" if success else "FAIL"
            result["error_msg"] = "" if success else "Monitoring timeout or error"
            tracker.set_result("success" if success else "failed")

        finally:
            # 关闭监控浏览器
            await monitor_page.close()
            await monitor_browser.close()
            await monitor_playwright.stop()

    except Exception as e:
        result["status"] = "FAIL"
        result["error_msg"] = str(e)[:100]
        tracker.set_result("failed", str(e)[:100])
        print(f"\n❌ 错误: {str(e)}")

    finally:
        # 保存追踪日志
        print("\n" + "=" * 60)
        print("保存追踪日志...")
        trace_manager = get_trace_manager()
        trace_paths = trace_manager.save_all()
        print(f"✅ 已保存 {len(trace_paths)} 条追踪日志到 traces/ 目录")
        print(f"追踪ID: {result['trace_id']}")

        # 关闭浏览器
        await executor.teardown()


if __name__ == "__main__":
    asyncio.run(main())
