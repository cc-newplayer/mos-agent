from datetime import datetime
from collections import defaultdict
from trace.tracker import get_trace_manager


def build_report(results):
    """生成日报 - 包含追踪日志"""
    if not results:
        return "没有测试结果"

    total = len(results)
    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    skipped = sum(1 for r in results if r["status"] == "SKIP")

    pass_rate = (passed / total * 100) if total > 0 else 0

    # 按模块统计
    module_stats = defaultdict(lambda: {"total": 0, "passed": 0})
    for r in results:
        module = str(r.get("module", "Unknown")).encode('utf-8', errors='ignore').decode('utf-8')
        module_stats[module]["total"] += 1
        if r["status"] == "PASS":
            module_stats[module]["passed"] += 1

    # 失败用例列表
    failed_cases = [r for r in results if r["status"] == "FAIL"]

    # 获取追踪日志
    trace_manager = get_trace_manager()
    trace_summary = trace_manager.get_trace_summary()

    # 生成日报文本
    report = []
    report.append("[MOS AutoTest Report] " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    report.append("")

    # 执行概览
    report.append("[Execution Summary]")
    report.append(f"  Total: {total} | Passed: {passed} | Failed: {failed} | Skipped: {skipped}")
    report.append(f"  Pass Rate: {pass_rate:.1f}%")
    report.append(f"  Total Duration: {sum(r['duration'] for r in results):.1f}s")
    report.append("")

    # 模块覆盖
    report.append("[Module Coverage]")
    for module, stats in sorted(module_stats.items()):
        report.append(f"  {module}: {stats['passed']}/{stats['total']} passed")
    report.append("")

    # 失败用例详情
    if failed_cases:
        report.append("[Failed Cases]")
        for case in failed_cases:
            trace_id = case.get("trace_id", "N/A")
            case_id = str(case.get('case_id', 'N/A')).encode('utf-8', errors='ignore').decode('utf-8')
            desc = str(case.get('description', '')).encode('utf-8', errors='ignore').decode('utf-8')
            error = str(case.get('error_msg', '')).encode('utf-8', errors='ignore').decode('utf-8')
            report.append(f"  {case_id} {desc}")
            report.append(f"    Error: {error}")
            report.append(f"    Trace ID: {trace_id}")
        report.append("")

    # 追踪日志摘要
    report.append("[Trace Summary]")
    report.append(f"  Success: {trace_summary['success']} | Failed: {trace_summary['failed']} | Pending: {trace_summary['pending']}")
    report.append("")

    # 追踪日志详情（仅显示失败的）
    failed_traces = [t for t in trace_summary['traces'] if t['result'] in ['failed', 'error']]
    if failed_traces:
        report.append("[Failed Trace Details]")
        for trace in failed_traces:
            report.append(f"  {trace['trace_id']}")
            case_id = str(trace.get('case_id', 'N/A')).encode('utf-8', errors='ignore').decode('utf-8')
            desc = str(trace.get('description', '')).encode('utf-8', errors='ignore').decode('utf-8')
            error = str(trace.get('error_msg', '')).encode('utf-8', errors='ignore').decode('utf-8')
            report.append(f"    Case: {case_id} - {desc}")
            report.append(f"    Error: {error}")
            if trace['steps']:
                report.append(f"    Steps: {len(trace['steps'])}")
                # 显示最后一个失败的步骤
                for step in reversed(trace['steps']):
                    if step['status'] == 'failed':
                        report.append(f"    Failed Step: {step['action']} - {step['target']}")
                        break
        report.append("")

    report.append("[Trace Storage]")
    report.append(f"  Location: mos-agent/traces/")
    report.append(f"  Total: {len(trace_summary['traces'])}")

    return "\n".join(report)


if __name__ == "__main__":
    # 测试
    test_results = [
        {
            "case_id": "MOS_001",
            "description": "导入 txt 文件",
            "module": "账号配置",
            "level": "P1",
            "status": "PASS",
            "error_msg": "",
            "duration": 5.2,
            "trace_id": "MOS_001_20260522_143000",
        },
        {
            "case_id": "MOS_002",
            "description": "导入 jsonl 文件",
            "module": "账号配置",
            "level": "P1",
            "status": "FAIL",
            "error_msg": "元素未找到",
            "duration": 3.1,
            "trace_id": "MOS_002_20260522_143100",
        },
    ]

    report = build_report(test_results)
    print(report)
