# MOS 运营值守 Agent

自动化测试框架，支持黑盒测试、日报生成、飞书推送。

## 快速开始

### 1. 环境准备

```bash
# 安装依赖
pip install playwright openpyxl requests

# 安装浏览器
playwright install chromium
```

### 2. 配置

编辑 `config.py`：
- `SYSTEM_URL`: 系统地址（已配置为 MOS）
- `LOGIN_USERNAME` / `LOGIN_PASSWORD`: 登录账号（已配置为 wly）
- `FEISHU_WEBHOOK`: 飞书 Webhook 地址（已配置）
- `EXCEL_FILE`: 测试用例文件路径

### 3. 运行

```bash
# 干运行（只生成报告，不推送）
python test_runner.py --dry-run

# 完整运行（推送到飞书）
python test_runner.py

# 只运行指定模块
python test_runner.py --module "账号配置"

# 只运行指定优先级
python test_runner.py --level P1
```

## 项目结构

```
mos-agent/
├── config.py                 # 配置文件（系统 URL、账号、Webhook）
├── test_runner.py            # 主入口（命令行工具）
├── README.md                 # 本文件
│
├── cases/
│   ├── __init__.py
│   └── loader.py             # 读取 Excel 测试用例
│
├── executor/
│   ├── __init__.py
│   └── runner.py             # Playwright 执行测试逻辑
│
├── report/
│   ├── __init__.py
│   └── builder.py            # 生成日报
│
├── feishu/
│   ├── __init__.py
│   └── sender.py             # 推送飞书
│
└── test_data/                # 测试数据文件（导入用）
    ├── test_accounts.txt
    ├── test_accounts.jsonl
    ├── empty.txt
    └── invalid.txt
```

## 日报格式

```
【MOS 自动化测试日报】2026-05-21

测试总数：47
通过：8（17.0%）
失败：1
跳过：38

失败用例：
- 用例编号 用例描述 | 错误：错误信息

模块覆盖：
  账号配置：8/16 通过
  事件源：0/4 通过
  ...

执行时间：62.3秒
```

## 当前支持的模块

| 模块 | 用例数 | 状态 | 支持的操作 |
|------|--------|------|----------|
| 账号配置 | 16 | ✅ 完成 | 导入、新建、编辑、删除 |
| 事件源 | 4 | ✅ 完成 | 手动编辑、对话框配置、添加监听 |
| 决策代理 | 11 | ⏳ 待实现 | - |
| 执行日志 | 3 | ⏳ 待实现 | - |
| 知识库 | 2 | ⏳ 待实现 | - |
| 管理员 | 7 | ⏳ 待实现 | - |
| 其他 | 4 | ⏳ 待实现 | - |

## 测试结果

**当前状态：**
- 总用例数：47
- 通过：8（17.0%）
- 失败：1
- 跳过：38

**账号模块测试通过的用例：**
- MOS_USER_001: 账号导入 txt 文件
- MOS_USER_002: 账号导入 jsonl 文件
- MOS_USER_005: 新建账号
- MOS_USER_006: 批量新建账号
- MOS_USER_008: 编辑账号
- MOS_USER_009: 编辑账号
- MOS_USER_010: 删除账号
- MOS_USER_011: 配置不同的IP

## 常见问题

### Q: 如何修改测试用例？
A: 编辑 `AI营销系统测试用例完整.xlsx` 文件，修改对应的步骤和预期结果。

### Q: 如何添加新的测试模块？
A: 
1. 在 `executor/runner.py` 中的 `execute_case` 方法添加模块判断
2. 实现对应的 `_test_xxx_module` 方法
3. 在方法中编写 Playwright 自动化脚本

### Q: 如何调试测试脚本？
A: 在 `config.py` 中设置 `HEADLESS = False`，这样会显示浏览器窗口。

### Q: 飞书推送失败怎么办？
A: 检查 `config.py` 中的 `FEISHU_WEBHOOK` 是否正确配置。

## 下一步计划

- [ ] 完善决策代理模块测试
- [ ] 完善其他模块测试
- [ ] 修复 NoneType 错误
- [ ] 设置定时任务（Windows 任务计划）
- [ ] 设计通用框架（YAML 配置 + 自动探测）

## 技术栈

- **自动化框架**: Playwright（异步）
- **Excel 处理**: openpyxl
- **HTTP 请求**: requests
- **消息推送**: 飞书 Webhook API

## 联系方式

如有问题，请联系开发团队。
