# 闭环测试工作流

通用的闭环测试工作流模块，支持所有类型的闭环测试。

## 文件说明

- **`test_loop_workflow.py`** - 主工作流脚本（入口点）
- **`loop_monitor.py`** - 实时监控模块
- **`loop_reporter.py`** - 报告生成和飞书推送模块
- **`LOOP_WORKFLOW_GUIDE.md`** - 使用指南
- **`LOOP_WORKFLOW_MULTI_SYSTEM.md`** - 多系统支持方案（补充文档）

## 快速开始

```bash
python loop_workflow/test_loop_workflow.py <case_id> <case_name> <instruction>
```

## 工作流阶段

1. **第1阶段**：输入指令（后台执行）
2. **第2阶段**：实时监控对话框内容（浏览器可见）
3. **第3阶段**：生成报告
4. **第4阶段**：推送到飞书

## 示例

```bash
# KOL 跟评闭环
python loop_workflow/test_loop_workflow.py 1 "KOL跟评闭环" "用一个引流号对@elonmusk最新的一篇推文执行KOL跟评闭环"

# 热点新闻蹭热度闭环
python loop_workflow/test_loop_workflow.py 2 "热点新闻蹭热度闭环" "用一个引流号找一个符合其人设的新闻热点执行蹭热度闭环"
```

## 输出

- **追踪日志**：`traces/` 目录
- **截图**：`screenshots/` 目录
- **飞书报告**：自动推送到配置的 Webhook

## 文档

- 详细使用指南：`LOOP_WORKFLOW_GUIDE.md`
- 多系统支持方案：`LOOP_WORKFLOW_MULTI_SYSTEM.md`
