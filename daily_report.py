# -*- coding: utf-8 -*-
import sys
import io
import json
from pathlib import Path
from datetime import datetime

if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from feishu.sender import send_to_feishu

today = datetime.now().strftime("%Y%m%d")
traces_dir = Path("traces")

# 统计结果
results = {"success": 0, "failed": 0, "skipped": 0}
failed_cases = []

for trace_file in traces_dir.glob(f"*{today}*.json"):
    try:
        with open(trace_file, encoding='utf-8') as f:
            data = json.load(f)
            result = data.get("result", "unknown")
            
            if result == "success":
                results["success"] += 1
            elif result == "failed":
                results["failed"] += 1
                failed_cases.append({
                    "case_id": data.get("case_id"),
                    "description": data.get("description"),
                })
            elif result == "skipped":
                results["skipped"] += 1
    except:
        pass

# 生成报告
total = sum(results.values())
pass_rate = results["success"] / (results["success"] + results["failed"]) * 100 if (results["success"] + results["failed"]) > 0 else 0

report = f"""MOS Agent 日报 - {datetime.now().strftime("%Y-%m-%d")}

测试统计
通过: {results['success']}
失败: {results['failed']}
跳过: {results['skipped']}
总计: {total}
通过率: {pass_rate:.1f}%

今天的工作
1. 完成闭环测试框架实现
   - 修复对话框内容监控逻辑
   - 实现轮询等待报告生成
   - 支持多种完成信号检测

2. 打包MOS Agent Skill
   - 整理核心模块和测试脚本
   - 创建README和配置示例
   - 生成mos-agent-skill.tar.gz

3. 测试闭环用例
   - Case 21: 热点新闻蹭热度 (监控中)
   - 发现长时间监控内容变错的问题

待处理
- 调查闭环测试长时间监控的问题
- 完成Case 21的测试
- 验证其他闭环用例
"""

print(report)

# 推送飞书
try:
    send_to_feishu(report)
    print("\n已推送到飞书")
except Exception as e:
    print(f"\n飞书推送失败: {e}")

