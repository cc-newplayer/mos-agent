#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整闭环测试脚本 - 测试所有需要轮询等待的闭环
包括：KOL跟评、热点新闻、油管转写、粉丝挖角、X投票等
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
    print("\n" + "=" * 70)
    print("🔄 MOS Agent 完整闭环测试")
    print("=" * 70)

    # 加载所有测试用例
    all_cases = load_test_cases()

    # 过滤出所有闭环相关的用例
    loop_cases = [
        c for c in all_cases
        if c.get('module') == '决策对话'
    ]

    print(f"\n📋 找到 {len(loop_cases)} 个决策对话用例")
    print("=" * 70)

    results = []
    passed = 0
    failed = 0
    skipped = 0

    for i, case in enumerate(loop_cases, 1):
        case_id = case.get('case_id', f'CASE_{i}')
        description = case.get('description', '')

        print(f"\n[{i}/{len(loop_cases)}] 执行用例 {case_id}")
        print(f"    描述: {description}")
        print("-" * 70)

        try:
            result = await run_test_case(case)
            results.append(result)

            if result['status'] == 'PASS':
                print(f"✅ PASS")
                passed += 1
            elif result['status'] == 'FAIL':
                print(f"❌ FAIL - {result.get('error_msg', '')[:80]}")
                failed += 1
            else:
                print(f"⊘ SKIP - {result.get('error_msg', '')[:80]}")
                skipped += 1

            print(f"    耗时: {result.get('duration', 0)}s")
            print(f"    追踪ID: {result.get('trace_id', 'N/A')}")

        except Exception as e:
            print(f"❌ ERROR - {str(e)[:80]}")
            failed += 1
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
    print("\n" + "=" * 70)
    print("💾 保存追踪日志...")
    trace_manager = get_trace_manager()
    trace_paths = trace_manager.save_all()
    print(f"✅ 已保存 {len(trace_paths)} 条追踪日志")

    # 生成报告
    print("\n📊 生成测试报告...")
    print("=" * 70)
    report = build_report(results)
    print(report)

    # 统计信息
    print("\n" + "=" * 70)
    print("📈 测试统计")
    print("=" * 70)
    print(f"总数: {len(results)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"⊘ 跳过: {skipped}")
    print(f"通过率: {passed / len(results) * 100:.1f}%" if results else "N/A")

    # 推送飞书
    print("\n📤 推送到飞书...")
    try:
        send_to_feishu(report, include_traces=True)
        print("✅ 已推送到飞书")
    except Exception as e:
        print(f"⚠️  飞书推送失败: {e}")

    print("\n" + "=" * 70)
    print("✨ 测试完成")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
