# 闭环测试工作流使用指南

## 概述

这是一个通用的闭环测试工作流，支持所有类型的闭环测试。工作流分为三个阶段：

1. **第1阶段**：输入指令（后台执行）
2. **第2阶段**：实时监控对话框内容（浏览器窗口可见）
3. **第3阶段**：生成报告

## 快速开始

### 基本用法

```bash
python test_loop_workflow.py <case_id> <case_name> <instruction>
```

### 示例

```bash
# KOL 跟评闭环
python test_loop_workflow.py 1 "KOL跟评闭环" "用一个引流号对@elonmusk最新的一篇推文执行KOL跟评闭环"

# 热点新闻蹭热度闭环
python test_loop_workflow.py 2 "热点新闻蹭热度闭环" "用一个引流号找一个符合其人设的新闻热点执行蹭热度闭环"

# 油管内容转写闭环
python test_loop_workflow.py 3 "油管内容转写闭环" "用一个引流号对YouTube频道最新视频执行内容转写闭环"

# 粉丝挖角闭环
python test_loop_workflow.py 4 "粉丝挖角闭环" "用一个引流号对@elonmusk的粉丝执行挖角闭环"

# X投票裂变引爆闭环
python test_loop_workflow.py 5 "X投票裂变引爆闭环" "用一个引流号对@elonmusk的投票执行裂变引爆闭环"
```

## 工作流详解

### 第1阶段：输入指令（后台执行）

- 导航到决策对话页面
- 点击一个决策对话
- 点击"新建对话"按钮
- 等待对话框出现
- 输入指令
- 发送指令（按Enter）

**特点**：
- 在后台浏览器中执行（HEADLESS=True）
- 用户看不到这个过程
- 快速完成（通常 < 1分钟）

### 第2阶段：实时监控对话框内容

- 打开新的可见浏览器窗口
- 每5分钟自动刷新一次
- 点击左侧对话卡片
- 获取右侧对话框内容
- 检查完成信号

**完成信号**：
- ✅ 成功：`"MarketingAI任务执行报告"`
- ❌ 规划失败：`"规划阶段出错"`
- ❌ 服务错误：`"Error code: 500"`
- ⚠️ 报告生成失败：`"报告生成失败"`

**特点**：
- 浏览器窗口可见，用户可以实时观看
- 自动刷新，无需手动操作
- 清晰展示执行进度

### 第3阶段：生成报告

- 收集监控数据
- 生成测试报告
- 保存追踪日志
- 输出报告信息

### 第4阶段：推送到飞书

- 格式化报告内容
- 推送到飞书 Webhook
- 确认推送成功

## 输出文件

### 追踪日志
- 位置：`mos-agent/traces/`
- 格式：JSON
- 内容：每个测试的完整操作链路

### 截图
- 位置：`mos-agent/screenshots/`
- 命名：`report_<number>_YYYYMMDD_HHMMSS.png`
- 内容：报告生成时的页面截图

## 监控参数

在 `test_loop_workflow.py` 中可以调整：

```python
# 检查间隔（秒）
check_interval=300  # 默认5分钟

# 最长等待时间（秒）
max_wait=3600  # 默认1小时
```

## 常见问题

### Q: 如何加快监控速度？
A: 修改 `check_interval` 参数，例如改为 `180`（3分钟）

### Q: 如何延长等待时间？
A: 修改 `max_wait` 参数，例如改为 `7200`（2小时）

### Q: 监控过程中可以关闭浏览器吗？
A: 不建议。关闭浏览器会中断监控。

### Q: 如何测试多个闭环？
A: 依次运行多个命令，例如：
```bash
python test_loop_workflow.py 1 "KOL跟评闭环" "..."
python test_loop_workflow.py 2 "热点新闻蹭热度闭环" "..."
python test_loop_workflow.py 3 "油管内容转写闭环" "..."
```

## 工作流优势

✅ **完全自动化** - 无需手动操作
✅ **实时可见** - 浏览器窗口显示执行进度
✅ **通用模板** - 支持所有闭环类型
✅ **完整追踪** - 记录每个操作步骤
✅ **自动推送** - 完成后自动推送到飞书
✅ **易于扩展** - 可轻松添加新的闭环类型

## 相关文件

- `test_loop_workflow.py` - 主工作流脚本
- `loop_monitor.py` - 监控模块
- `loop_reporter.py` - 报告生成模块
- `executor/runner.py` - 执行器
- `trace/tracker.py` - 追踪系统
