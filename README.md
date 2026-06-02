# MOS Agent - 营销系统自动化测试框架

基于 Playwright 的自动化测试框架，用于 MOS（Marketing Operating System）的端到端测试。支持两种测试模式：操作用例批量验证 和 闭环工作流监控。

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                    入口脚本                          │
├──────────────┬──────────────┬───────────────────────┤
│ test_runner  │ test_single  │ loop_workflow/         │
│ (全量操作)   │ (单条操作)   │ test_loop_workflow    │
│              │              │ (单个闭环)             │
├──────────────┴──────────────┼───────────────────────┤
│       executor/             │  skills/              │
│  runner.py (操作执行器)     │  batch_executor/      │
│  loop_handler.py (轮询)    │  (批量闭环执行器)     │
├─────────────────────────────┴───────────────────────┤
│  loop_workflow/                                      │
│  loop_monitor.py (实时监控) + loop_reporter.py      │
├─────────────────────────────────────────────────────┤
│  trace/ (操作追踪)  │  feishu/ (飞书推送)           │
└─────────────────────────────────────────────────────┘
```

## 两条测试线

### 1. 操作用例测试

从 Excel 加载用例，自动执行 UI 操作并验证结果。覆盖账号管理、事件源配置、定时任务等模块。

```bash
# 跑全量用例
python test_runner.py

# 跑单条
python test_single_case.py 22
```

### 2. 闭环工作流测试

向系统发送一条自然语言指令，系统自主执行完整业务闭环（调研→决策→执行→生成报告）。测试框架负责：输入指令 → 实时监控执行状态 → 检测完成信号 → 生成报告 → 推送飞书。

```bash
# 单个闭环
python loop_workflow/test_loop_workflow.py 1 "KOL跟评" "用一个引流号对elonmusk最新的一篇帖子执行KOL跟评闭环"

# 批量闭环（从 Excel 读取）
python skills/batch_executor/run_batch.py loops.xlsx
```

## 核心能力

- 操作追踪：每条用例的完整操作链路（导航→查找→点击→验证）记录为 JSON，可追溯
- 实时监控：闭环执行期间定时轮询页面内容，检测成功/失败信号
- 信号检测：识别"任务执行报告"（成功）、"规划阶段出错"（失败）、"Error code: 500"（服务异常）
- 飞书推送：测试结果自动推送到飞书群
- 批量执行：支持 Excel/JSON/CSV 输入，依次执行多个闭环并汇总报告

## 项目结构

```
mos-agent/
├── config.example.py          # 配置模板（复制为 config.py 使用）
├── test_runner.py             # 全量操作用例入口
├── test_single_case.py        # 单条操作用例入口
├── daily_report.py            # 从 trace 生成日报
│
├── cases/
│   └── loader.py              # Excel 用例加载器
│
├── executor/
│   ├── runner.py              # 操作用例执行器（Playwright）
│   └── loop_handler.py        # 闭环轮询处理器
│
├── loop_workflow/
│   ├── test_loop_workflow.py  # 闭环工作流入口
│   ├── loop_monitor.py        # 实时监控模块
│   └── loop_reporter.py       # 报告生成 + 飞书推送
│
├── skills/
│   └── batch_executor/        # 批量闭环执行器
│       ├── run_batch.py       # 入口
│       ├── batch_loader.py    # 多格式文件加载
│       ├── batch_executor.py  # 执行逻辑
│       └── batch_reporter.py  # 汇总报告
│
├── trace/
│   └── tracker.py             # 操作追踪系统
│
├── feishu/
│   └── sender.py              # 飞书 Webhook 推送
│
└── report/
    └── builder.py             # 报告构建器
```

## 快速开始

```bash
# 安装依赖
pip install playwright openpyxl requests

# 安装浏览器
playwright install chromium

# 配置
cp config.example.py config.py
# 编辑 config.py 填入系统地址、账号密码、飞书 Webhook

# 运行操作用例测试
python test_runner.py

# 运行闭环测试
python loop_workflow/test_loop_workflow.py 1 "测试名称" "测试指令"
```

## 技术栈

- Playwright (async) — 浏览器自动化
- openpyxl — Excel 用例加载
- requests — 飞书 Webhook 推送
