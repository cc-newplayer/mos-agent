#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KOL 闭环测试脚本 - 测试需要轮询等待报告生成的闭环
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
from report.builder import build_report
from feishu.sender import send_to_feishu
from trace.tracker import get_trace_manager


async def main():
    print("=" * 60)
    print("单个 KOL 闭环测试 - @elonmusk")
    print("=" * 60)

    # 创建单个 KOL 闭环用例
    case = {
        "case_id": "KOL_ELONMUSK",
        "description": "KOL跟评闭环 - @elonmusk",
        "module": "决策对话",
        "level": "P1",
        "type": "closedloop",
        "instruction": "用一个引流号对@elonmusk最新的一篇推文执行KOL跟评闭环",
    }

    loop_cases = [case]

    print(f"\n测试用例: {case['case_id']} - {case['description']}")
    print(f"指令: {case['instruction']}")
    print("=" * 60)

    results = []
    for i, case in enumerate(loop_cases, 1):
        case_id = case.get('case_id', f'CASE_{i}')
        description = case.get('description', '')

        print(f"\n[{i}/{len(loop_cases)}] 执行用例 {case_id}: {description}")
        print("-" * 60)

        try:
            result = await run_test_case(case)
            results.append(result)

            status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⊘"
            print(f"{status_icon} 结果: {result['status']}")
            if result.get('error_msg'):
                print(f"   错误: {result['error_msg'][:100]}")
            print(f"   耗时: {result.get('duration', 0)}s")
            print(f"   追踪ID: {result.get('trace_id', 'N/A')}")

        except Exception as e:
            print(f"❌ 异常: {str(e)[:100]}")
            results.append({
                'case_id': case_id,
                'description': description,
                'module': case.get('module', 'Unknown'),
                'level': case.get('level', 'P3'),
                'status': 'ERROR',
                'error_msg': str(e)[:100],
                'duration': 0,
                'trace_id': 'N/A'
            })

    # 保存追踪日志
    print("\n" + "=" * 60)
    print("保存追踪日志...")
    trace_manager = get_trace_manager()
    trace_paths = trace_manager.save_all()
    print(f"已保存 {len(trace_paths)} 条追踪日志到 traces/ 目录")

    # 生成报告
    print("\n生成测试报告...")
    print("=" * 60)
    report = build_report(results)
    print(report)

    # 推送飞书
    print("\n推送到飞书...")
    try:
        send_to_feishu(report, include_traces=True)
        print("✅ 已推送到飞书")
    except Exception as e:
        print(f"⚠️  飞书推送失败: {e}")


if __name__ == "__main__":
    asyncio.run(main())
