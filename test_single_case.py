#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单个用例测试脚本 - 只测试指定的一个用例
用法: python test_single_case.py <case_id>
例如: python test_single_case.py 22
"""
import asyncio
import sys
import io
from pathlib import Path

# 修复编码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent))

from cases.loader import load_test_cases
from executor.runner import run_test_case
from trace.tracker import get_trace_manager


async def main():
    if len(sys.argv) < 2:
        print("用法: python test_single_case.py <case_id>")
        print("例如: python test_single_case.py 22")
        sys.exit(1)

    target_case_id = sys.argv[1]

    # 加载所有测试用例
    all_cases = load_test_cases()

    # 查找指定的用例
    target_case = None
    for case in all_cases:
        if str(case.get('case_id')) == str(target_case_id):
            target_case = case
            break

    if not target_case:
        print(f"❌ 找不到用例 {target_case_id}")
        sys.exit(1)

    print("=" * 70)
    print(f"执行单个用例: {target_case_id}")
    print("=" * 70)
    print(f"描述: {target_case.get('description', '')}")
    print(f"模块: {target_case.get('module', '')}")
    print(f"类型: {target_case.get('type', 'default')}")
    if target_case.get('instruction'):
        print(f"指令: {target_case.get('instruction')}")
    print("=" * 70 + "\n")

    try:
        result = await run_test_case(target_case)

        status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⊘"
        print(f"\n{status_icon} 结果: {result['status']}")
        if result.get('error_msg'):
            print(f"   错误: {result['error_msg']}")
        print(f"   耗时: {result.get('duration', 0)}s")
        print(f"   追踪ID: {result.get('trace_id', 'N/A')}")

    except Exception as e:
        print(f"❌ 异常: {str(e)}")

    # 保存追踪日志
    print("\n" + "=" * 70)
    trace_manager = get_trace_manager()
    trace_paths = trace_manager.save_all()
    print(f"✅ 已保存追踪日志到 traces/ 目录")


if __name__ == "__main__":
    asyncio.run(main())
