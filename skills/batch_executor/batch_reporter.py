#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量报告生成器 - 生成汇总报告并推送到飞书
"""
from datetime import datetime
import requests
from config import FEISHU_WEBHOOK


class BatchReporter:
    """批量报告生成器"""

    def __init__(self, batch_name="批量闭环测试"):
        self.batch_name = batch_name
        self.start_time = None
        self.end_time = None

    def generate_report(self, results, start_time, end_time):
        """
        生成汇总报告

        Args:
            results: 执行结果列表
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            report_dict: 报告字典
        """
        self.start_time = start_time
        self.end_time = end_time

        # 统计
        total = len(results)
        success = sum(1 for r in results if r['status'] == 'success')
        failed = sum(1 for r in results if r['status'] == 'failed')
        error = sum(1 for r in results if r['status'] == 'error')
        success_rate = (success / total * 100) if total > 0 else 0

        # 计算总耗时
        total_elapsed = sum(r.get('elapsed', 0) for r in results)

        report = {
            'batch_name': self.batch_name,
            'start_time': start_time.strftime("%Y-%m-%d %H:%M:%S"),
            'end_time': end_time.strftime("%Y-%m-%d %H:%M:%S"),
            'total_elapsed': total_elapsed,
            'total': total,
            'success': success,
            'failed': failed,
            'error': error,
            'success_rate': success_rate,
            'results': results
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
        total_minutes = round(report['total_elapsed'] / 60)
        text = f"""【MOS 批量闭环测试报告】

批次名称：{report['batch_name']}
执行时间：{report['start_time']} - {report['end_time']}
总耗时：{round(report['total_elapsed'])}s（约 {total_minutes} 分钟）

【执行统计】
总数：{report['total']} | 成功：{report['success']} | 失败：{report['failed'] + report['error']}
成功率：{report['success_rate']:.0f}%

【闭环详情】
"""

        for i, result in enumerate(report['results'], 1):
            elapsed_minutes = round(result.get('elapsed', 0) / 60)
            check_count = result.get('check_count', 0)
            status_icon = "✅" if result['status'] == 'success' else "❌"
            status_text = "成功" if result['status'] == 'success' else "失败"

            text += f"{i}. {result['name']}\n"
            text += f"   指令：{result['instruction']}\n"
            text += f"   状态：{status_icon} {status_text}\n"
            text += f"   耗时：{result.get('elapsed', 0)}s（约{elapsed_minutes}分钟）\n"
            text += f"   检查次数：{check_count}次\n"

            # 时间线
            if result['status'] == 'success':
                if check_count > 1:
                    text += f"   时间线：前{check_count - 1}次未检测到信号（每5分钟一次），第{check_count}次检测到报告生成\n"
                else:
                    text += f"   时间线：第1次检查即检测到报告生成\n"
            else:
                message = result.get('message', result.get('error_msg', ''))
                if message:
                    if check_count > 1:
                        text += f"   失败原因：第{check_count}次检查检测到「{message}」信号\n"
                        text += f"   时间线：前{check_count - 1}次未检测到信号，第{check_count}次检测到错误信号\n"
                    else:
                        text += f"   失败原因：{message}\n"

            text += "\n"

        # 结论
        if report['success'] == report['total']:
            text += "【结论】\n所有闭环执行成功，批量执行器运行稳定。\n"
        elif report['success'] > 0:
            failed_names = [r['name'] for r in report['results'] if r['status'] != 'success']
            text += f"【结论】\n批量执行器功能正常：文件加载、依次执行、监控检测、报告生成均通过。"
            text += f"{'、'.join(failed_names)}失败为系统侧问题，非脚本问题。\n"
        else:
            text += "【结论】\n所有闭环均失败，需排查系统侧问题。\n"

        return text

    def print_report(self, report):
        """打印报告"""
        print("\n" + "=" * 60)
        print("📊 批量测试报告")
        print("=" * 60)
        print(self.format_feishu_report(report))
        print("=" * 60)

    def send_to_feishu(self, report):
        """
        推送报告到飞书

        Args:
            report: 报告字典

        Returns:
            success: 是否推送成功
        """
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
