import requests
import json
from pathlib import Path
from config import FEISHU_WEBHOOK
from trace.tracker import get_trace_manager


def send_to_feishu(report_text, include_traces=True):
    """推送日报到飞书"""
    if not FEISHU_WEBHOOK:
        print("飞书 Webhook 未配置，日报内容：")
        print(report_text)
        return False

    # 构建消息内容
    message_content = report_text

    # 如果需要，添加追踪日志链接
    if include_traces:
        trace_manager = get_trace_manager()
        trace_paths = trace_manager.save_all()

        if trace_paths:
            message_content += "\n\n📎 追踪日志文件："
            for path in trace_paths:
                message_content += f"\n  - {path.name}"

    payload = {
        "msg_type": "text",
        "content": {
            "text": message_content
        }
    }

    try:
        response = requests.post(FEISHU_WEBHOOK, json=payload, timeout=10)
        if response.status_code == 200:
            print("日报已推送到飞书")
            return True
        else:
            print(f"推送失败，状态码：{response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"推送异常：{e}")
        return False


def send_trace_details_to_feishu(trace_id):
    """推送单个追踪日志详情到飞书"""
    if not FEISHU_WEBHOOK:
        print("飞书 Webhook 未配置")
        return False

    trace_manager = get_trace_manager()
    traces = trace_manager.get_all_traces()

    # 查找对应的追踪日志
    target_trace = None
    for trace in traces:
        if trace['trace_id'] == trace_id:
            target_trace = trace
            break

    if not target_trace:
        print(f"追踪日志 {trace_id} 不存在")
        return False

    # 构建详细信息
    details = f"""【追踪日志详情】{trace_id}

用例：{target_trace['case_id']} - {target_trace['description']}
结果：{target_trace['result']}
耗时：{target_trace['duration']:.2f}秒

操作步骤：
"""

    for i, step in enumerate(target_trace['steps'], 1):
        details += f"\n{i}. {step['action']} - {step['target']}"
        details += f"\n   状态：{step['status']}"
        if step['details']:
            details += f"\n   详情：{json.dumps(step['details'], ensure_ascii=False)}"

    if target_trace['error_msg']:
        details += f"\n\n错误信息：{target_trace['error_msg']}"

    payload = {
        "msg_type": "text",
        "content": {
            "text": details
        }
    }

    try:
        response = requests.post(FEISHU_WEBHOOK, json=payload, timeout=10)
        if response.status_code == 200:
            print(f"追踪日志 {trace_id} 已推送到飞书")
            return True
        else:
            print(f"推送失败，状态码：{response.status_code}")
            return False
    except Exception as e:
        print(f"推送异常：{e}")
        return False


if __name__ == "__main__":
    test_report = """【MOS 自动化测试日报】2026-05-22

📊 执行概览
  总数：2 | 通过：1 | 失败：1 | 跳过：0
  通过率：50.0%
  执行时间：8.3秒

📋 模块覆盖
  账号配置：1/2 通过

❌ 失败用例
  MOS_002 导入 jsonl 文件
    错误：元素未找到
    追踪ID：MOS_002_20260522_143100"""

    send_to_feishu(test_report)
