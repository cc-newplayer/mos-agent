import asyncio
import argparse
import sys
import io

# 修复编码问题，支持 emoji 和中文
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from cases.loader import load_test_cases
from executor.runner import run_test_case
from report.builder import build_report
from feishu.sender import send_to_feishu
from trace.tracker import get_trace_manager


async def main():
    parser = argparse.ArgumentParser(description="MOS 自动化测试 Agent")
    parser.add_argument("--module", help="只运行指定模块的用例")
    parser.add_argument("--level", help="只运行指定优先级的用例")
    parser.add_argument("--exclude-module", help="排除指定模块的用例")
    parser.add_argument("--cases", help="只运行指定的用例ID（逗号分隔）")
    parser.add_argument("--dry-run", action="store_true", help="只生成报告不推送")
    args = parser.parse_args()

    print("加载测试用例...")
    cases = load_test_cases()

    # 过滤用例
    if args.module:
        cases = [c for c in cases if c["module"] == args.module]
    if args.level:
        cases = [c for c in cases if c["level"] == args.level]
    if args.exclude_module:
        cases = [c for c in cases if c["module"] != args.exclude_module]
    if args.cases:
        case_ids = [cid.strip() for cid in args.cases.split(",")]
        cases = [c for c in cases if c["case_id"] in case_ids]

    print(f"准备执行 {len(cases)} 条用例")

    # 执行用例
    results = []
    for i, case in enumerate(cases, 1):
        print(f"[{i}/{len(cases)}] 执行 {case['case_id']} - {case['description']}")
        try:
            result = await run_test_case(case)
            results.append(result)
            print(f"  结果：{result['status']} (追踪ID: {result.get('trace_id', 'N/A')})")
        except Exception as e:
            print(f"  异常：{e}")
            results.append({
                "case_id": case["case_id"],
                "description": case["description"],
                "module": case["module"],
                "level": case["level"],
                "status": "ERROR",
                "error_msg": str(e),
                "duration": 0,
                "trace_id": "N/A",
            })

    # 保存追踪日志
    print("\n保存追踪日志...")
    trace_manager = get_trace_manager()
    trace_paths = trace_manager.save_all()
    print(f"已保存 {len(trace_paths)} 条追踪日志")

    # 生成日报
    print("\n生成日报...")
    report = build_report(results)
    print(report)

    # 推送飞书
    if not args.dry_run:
        print("\n推送到飞书...")
        send_to_feishu(report, include_traces=True)
    else:
        print("\n(--dry-run 模式，不推送)")


if __name__ == "__main__":
    asyncio.run(main())

