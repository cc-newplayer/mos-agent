#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量闭环测试 - 入口脚本

用法：
  python run_batch.py batch_loops.xlsx
  python run_batch.py batch_loops.json
  python run_batch.py batch_loops.csv
  python run_batch.py batch_loops.xlsx --output results/
"""
import asyncio
import argparse
import sys
import io
from pathlib import Path
from datetime import datetime

# 修复编码问题
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from batch_loader import BatchLoader
from batch_executor import BatchExecutor
from batch_reporter import BatchReporter


async def main():
    parser = argparse.ArgumentParser(
        description="MOS 批量闭环测试",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python run_batch.py batch_loops.xlsx
  python run_batch.py batch_loops.json
  python run_batch.py batch_loops.csv --output results/
        """
    )
    parser.add_argument('file', help='测试文件路径（.xlsx/.json/.csv）')
    parser.add_argument('--output', help='输出目录（可选）', default=None)
    parser.add_argument('--dry-run', action='store_true', help='只生成报告不推送到飞书')

    args = parser.parse_args()

    # 验证文件
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)

    print("=" * 60)
    print("📋 批量闭环测试")
    print("=" * 60)
    print(f"文件：{file_path}")
    print("=" * 60)

    try:
        # 【第1步】加载文件
        print("\n[步骤1] 加载测试文件...")
        loader = BatchLoader()
        loops = loader.load(file_path)

        if not loops:
            print("❌ 文件中没有闭环数据")
            sys.exit(1)

        print(f"✓ 已加载 {len(loops)} 个闭环")
        for i, loop in enumerate(loops, 1):
            print(f"  {i}. {loop['name']}")

        # 【第2步】执行所有闭环
        print("\n[步骤2] 执行所有闭环...")
        start_time = datetime.now()

        executor = BatchExecutor()
        results = await executor.run(loops)

        end_time = datetime.now()

        # 【第3步】生成报告
        print("\n[步骤3] 生成汇总报告...")
        reporter = BatchReporter(batch_name=f"批量闭环测试 - {file_path.stem}")
        report = reporter.generate_report(results, start_time, end_time)

        reporter.print_report(report)

        # 【第4步】推送到飞书
        print("\n[步骤4] 推送到飞书...")
        if args.dry_run:
            print("⊘ 跳过推送（--dry-run 模式）")
        else:
            reporter.send_to_feishu(report)

        print("\n" + "=" * 60)
        print("✅ 批量测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
