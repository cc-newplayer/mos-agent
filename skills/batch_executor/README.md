# 批量闭环执行器

批量执行闭环测试，支持从 Excel/JSON/CSV 文件加载闭环列表，依次执行，生成汇总报告。

## 快速开始

### 基本用法

```bash
python run_batch.py <file> [--output <dir>] [--dry-run]
```

### 示例

```bash
# 执行 Excel 文件
python run_batch.py batch_loops.xlsx

# 执行 JSON 文件
python run_batch.py batch_loops.json

# 执行 CSV 文件
python run_batch.py batch_loops.csv

# 指定输出目录
python run_batch.py batch_loops.xlsx --output results/

# 只生成报告不推送到飞书
python run_batch.py batch_loops.xlsx --dry-run
```

## 文件格式

### Excel 格式（推荐）

```
| case_id | name           | instruction                                    |
|---------|----------------|------------------------------------------------|
| 1       | KOL跟评闭环    | 用一个引流号对@elonmusk最新的一篇推文执行...  |
| 2       | 热点新闻蹭热度 | 用一个引流号找一个符合其人设的新闻热点...     |
| 3       | 油管内容转写   | 用一个引流号对YouTube频道最新视频执行...      |
```

### JSON 格式

```json
{
  "loops": [
    {
      "case_id": 1,
      "name": "KOL跟评闭环",
      "instruction": "用一个引流号对@elonmusk最新的一篇推文执行..."
    },
    {
      "case_id": 2,
      "name": "热点新闻蹭热度",
      "instruction": "用一个引流号找一个符合其人设的新闻热点..."
    }
  ]
}
```

### CSV 格式

```csv
case_id,name,instruction
1,KOL跟评闭环,用一个引流号对@elonmusk最新的一篇推文执行...
2,热点新闻蹭热度,用一个引流号找一个符合其人设的新闻热点...
```

## 工作流程

```
加载文件
  ↓
解析闭环列表
  ↓
[循环] 逐个执行闭环
  ├─ 执行第1个闭环
  ├─ 工作流内部检测完成信号
  ├─ 生成单个报告
  ├─ 等待 5 秒
  ├─ 执行第2个闭环
  └─ ...
  ↓
生成汇总报告
  ↓
推送到飞书
```

## 输出

### 追踪日志
- 位置：`traces/` 目录
- 格式：JSON
- 内容：每个闭环的完整操作链路

### 截图
- 位置：`screenshots/` 目录
- 格式：PNG
- 内容：报告生成时的页面截图

### 飞书报告
- 自动推送到配置的 Webhook
- 包含执行统计、单个结果、建议等

## 配置

在 `config.py` 中配置：

```python
# 系统 URL
SYSTEM_URL = "https://marketing-os.tnt-pub.com"

# 登录凭证
LOGIN_USERNAME = "wly"
LOGIN_PASSWORD = "wly"

# 飞书 Webhook
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/..."
```

## 文件说明

- **`run_batch.py`** - 入口脚本
- **`batch_loader.py`** - 文件加载器（支持 Excel/JSON/CSV）
- **`batch_executor.py`** - 批量执行器（核心逻辑）
- **`batch_reporter.py`** - 报告生成器
- **`examples/`** - 示例文件目录

## 工作原理

1. **加载阶段**：从文件中读取闭环列表
2. **执行阶段**：依次执行每个闭环
   - 调用 `loop_workflow` 工作流
   - 工作流内部监控对话框内容
   - 检测完成信号（"MarketingAI任务执行报告"等）
   - 识别到信号就返回结果
3. **报告阶段**：生成汇总报告
4. **推送阶段**：推送到飞书

## 完成检测

工作流内部已经实现了完成检测：
- ✅ 监控对话框内容
- ✅ 检测完成信号
- ✅ 识别到信号就返回

batch_executor 直接使用工作流的检测结果，无需重复检测。

## 注意事项

1. **一次一个闭环** - 避免账号不足
2. **保持浏览器打开** - 不要中断监控
3. **查看追踪日志** - 了解执行细节
4. **检查飞书报告** - 确认推送成功

## 示例文件

见 `examples/batch_loops.xlsx` 目录
