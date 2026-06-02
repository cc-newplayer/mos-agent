# 批量闭环执行器 - 快速使用指南

## 📁 文件结构

```
skills/batch_executor/
├── __init__.py
├── run_batch.py              # 入口脚本
├── batch_loader.py           # 文件加载器
├── batch_executor.py         # 批量执行器（核心）
├── batch_reporter.py         # 报告生成器
├── README.md                 # 详细文档
└── examples/
    └── batch_loops.xlsx      # 示例文件
```

## 🚀 快速开始

### 1. 准备测试文件

创建 Excel 文件（或使用 `examples/batch_loops.xlsx`）：

| case_id | name           | instruction                                    |
|---------|----------------|------------------------------------------------|
| 1       | KOL跟评闭环    | 用一个引流号对@elonmusk最新的一篇推文执行...  |
| 2       | 热点新闻蹭热度 | 用一个引流号找一个符合其人设的新闻热点...     |
| 3       | 油管内容转写   | 用一个引流号对YouTube频道最新视频执行...      |

### 2. 运行批量测试

```bash
# 基本用法
python skills/batch_executor/run_batch.py batch_loops.xlsx

# 只生成报告不推送到飞书
python skills/batch_executor/run_batch.py batch_loops.xlsx --dry-run

# 支持 JSON 和 CSV
python skills/batch_executor/run_batch.py batch_loops.json
python skills/batch_executor/run_batch.py batch_loops.csv
```

### 3. 查看结果

- **追踪日志**：`traces/` 目录
- **截图**：`screenshots/` 目录
- **飞书报告**：自动推送到配置的 Webhook

## 📊 工作流程

```
加载文件
  ↓
【循环】逐个执行闭环
  ├─ 执行闭环 1
  ├─ 工作流检测完成信号
  ├─ 等待 5 秒
  ├─ 执行闭环 2
  └─ ...
  ↓
生成汇总报告
  ↓
推送到飞书
```

## 🔑 关键特性

✅ **支持多种格式**：Excel、JSON、CSV
✅ **自动检测完成**：工作流内部检测完成信号
✅ **依次执行**：一个接一个，避免账号不足
✅ **完整追踪**：记录每个闭环的操作链路
✅ **汇总报告**：统计成功率、耗时等
✅ **自动推送**：完成后自动推送到飞书

## 📝 文件格式

### Excel（推荐）
- 第一行：表头（case_id, name, instruction）
- 后续行：数据

### JSON
```json
{
  "loops": [
    {"case_id": 1, "name": "...", "instruction": "..."}
  ]
}
```

### CSV
```csv
case_id,name,instruction
1,KOL跟评闭环,用一个引流号对@elonmusk...
```

## ⚙️ 配置

在 `config.py` 中配置：
- `SYSTEM_URL` - 系统地址
- `LOGIN_USERNAME` - 登录用户名
- `LOGIN_PASSWORD` - 登录密码
- `FEISHU_WEBHOOK` - 飞书 Webhook

## 💡 使用建议

1. **先用示例文件测试**：`examples/batch_loops.xlsx`
2. **查看详细文档**：`README.md`
3. **监控执行过程**：浏览器窗口会显示实时进度
4. **检查追踪日志**：了解每个闭环的详细执行过程

## 🎯 下一步

- 测试批量执行功能
- 根据需要调整闭环列表
- 集成到 Agent 中
