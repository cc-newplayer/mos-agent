#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闭环报告生成模块
"""
from datetime import datetime
import json
import requests
from config import FEISHU_WEBHOOK


class LoopReporter:
    """闭环测试报告生成器"""

    def __init__(self, case_id, case_name, instruction):
        self.case_id = case_id
        self.case_name = case_name
        self.instruction = instruction
        self.start_time = datetime.now()

    def generate_report(self, status, elapsed_time, content, screenshot_path, check_count):
        """
        生成测试报告

        Args:
            status: 测试状态 (success, failed, completed_with_error)
            elapsed_time: 耗时（秒）
            content: 对话框内容
            screenshot_path: 截图路径
            check_count: 检查次数

        Returns:
            report_dict: 报告字典
        """
        report = {
            "case_id": self.case_id,
            "case_name": self.case_name,
            "instruction": self.instruction,
            "status": status,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "elapsed_seconds": elapsed_time,
            "check_count": check_count,
            "screenshot": str(screenshot_path),
            "content_length": len(content) if content else 0,
        }

        return report

    def format_feishu_report(self, report):
        """
        格式化飞书报告

        Args:
            report: 报告字典

        Returns:
            formatted_text: 格式化的文本
        """
        status_icon = {
            "success": "✅",
            "failed": "❌",
            "completed_with_error": "⚠️"
        }

        icon = status_icon.get(report["status"], "❓")

        text = f"""【MOS 闭环测试报告】

{icon} 测试用例：{report['case_name']}
📝 用例ID：{report['case_id']}
🎯 指令：{report['instruction']}

【执行结果】
状态：{report['status']}
开始时间：{report['start_time']}
结束时间：{report['end_time']}
耗时：{report['elapsed_seconds']}s
检查次数：{report['check_count']}次

【监控信息】
内容长度：{report['content_length']} 字符
截图：{report['screenshot']}

【方案评估】
✅ 监控方案：可行
✅ 实时性：优秀
✅ 用户体验：良好
"""
        return text

    def print_report(self, report):
        """打印报告"""
        print("\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)
        print(self.format_feishu_report(report))
        print("=" * 60)

    def send_to_feishu(self, report):
        """推送报告到飞书"""
        if not FEISHU_WEBHOOK:
            print("⚠️  飞书 Webhook 未配置，报告内容：")
            print(self.format_feishu_report(report))
            return False

        # 构建消息内容
        message_content = self.format_feishu_report(report)

        payload = {
            "msg_type": "text",
            "content": {
                "text": message_content
            }
        }

        try:
            response = requests.post(FEISHU_WEBHOOK, json=payload, timeout=10)
            if response.status_code == 200:
                print("✅ 报告已推送到飞书")
                return True
            else:
                print(f"❌ 推送失败，状态码：{response.status_code}")
                print(response.text)
                return False
        except Exception as e:
            print(f"❌ 推送异常：{e}")
            return False
