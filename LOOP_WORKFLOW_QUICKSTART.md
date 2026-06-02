# 闭环测试工作流 - 快速开始

## 📁 文件夹结构

```
mos-agent/
├── loop_workflow/              # 闭环测试工作流（新增）
│   ├── __init__.py
│   ├── README.md               # 模块说明
│   ├── test_loop_workflow.py   # 主脚本（入口点）
│   ├── loop_monitor.py         # 监控模块
│   ├── loop_reporter.py        # 报告模块
│   ├── LOOP_WORKFLOW_GUIDE.md  # 使用指南
│   └── LOOP_WORKFLOW_MULTI_SYSTEM.md  # 多系统支持方案
├── executor/
├── trace/
├── feishu/
└── ...
```

## 🚀 快速开始

### 基本用法

```bash
python loop_workflow/test_loop_workflow.py <case_id> <case_name> <instruction>
```

### 示例

```bash
# KOL 跟评闭环
python loop_workflow/test_loop_workflow.py 1 "KOL跟评闭环" "用一个引流号对@elonmusk最新的一篇推文执行KOL跟评闭环"

# 热点新闻蹭热度闭环
python loop_workflow/test_loop_workflow.py 2 "热点新闻蹭热度闭环" "用一个引流号找一个符合其人设的新闻热点执行蹭热度闭环"

# 油管内容转写闭环
python loop_workflow/test_loop_workflow.py 3 "油管内容转写闭环" "用一个引流号对YouTube频道最新视频执行内容转写闭环"

# 粉丝挖角闭环
python loop_workflow/test_loop_workflow.py 4 "粉丝挖角闭环" "用一个引流号对@elonmusk的粉丝执行挖角闭环"

# X投票裂变引爆闭环
python loop_workflow/test_loop_workflow.py 5 "X投票裂变引爆闭环" "用一个引流号对@elonmusk的投票执行裂变引爆闭环"
```

## 📊 工作流阶段

1. **第1阶段**：输入指令（后台执行）
   - 导航到决策对话页面
   - 点击对话、新建对话、输入指令、发送

2. **第2阶段**：实时监控（浏览器可见）
   - 打开可见浏览器窗口
   - 每5分钟自动刷新检查
   - 监控对话框内容

3. **第3阶段**：生成报告
   - 收集监控数据
   - 生成测试报告
   - 保存追踪日志

4. **第4阶段**：推送到飞书
   - 格式化报告
   - 推送到飞书 Webhook
   - 确认推送成功

## 📁 输出文件

- **追踪日志**：`traces/` 目录（JSON 格式）
- **截图**：`screenshots/` 目录（PNG 格式）
- **飞书报告**：自动推送到配置的 Webhook

## 📖 详细文档

- **使用指南**：`loop_workflow/LOOP_WORKFLOW_GUIDE.md`
- **多系统支持**：`loop_workflow/LOOP_WORKFLOW_MULTI_SYSTEM.md`

## ✨ 工作流优势

✅ 完全自动化
✅ 实时可见（浏览器窗口显示进度）
✅ 通用模板（所有闭环都能用）
✅ 完整追踪（记录每个操作步骤）
✅ 自动推送（完成后自动推送到飞书）
✅ 易于扩展（支持多系统）

## 🔧 配置

在 `config.py` 中配置：

```python
# 系统 URL
SYSTEM_URL = "https://marketing-os.tnt-pub.com"

# 登录凭证
LOGIN_USERNAME = "wly"
LOGIN_PASSWORD = "wly"

# 飞书 Webhook
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/..."

# 浏览器配置
HEADLESS = True  # 前台脚本后台执行
TIMEOUT = 30000  # 30秒超时
```

## 💡 使用建议

1. **一次测试一个闭环** - 避免账号不足
2. **保持浏览器打开** - 不要中断监控
3. **查看追踪日志** - 了解执行细节
4. **检查飞书报告** - 确认推送成功

## 🎯 下一步

- 支持更多闭环类型
- 支持其他系统（参考 `LOOP_WORKFLOW_MULTI_SYSTEM.md`）
- 构建 Web 界面
- 集成 CI/CD 流程
