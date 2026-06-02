# MOS Agent Skill 打包清单

## 要包含的文件/目录

### 核心模块
- [ ] cases/loader.py - 用例加载
- [ ] cases/test_cases.xlsx - 测试用例文件
- [ ] executor/runner.py - 测试执行器
- [ ] executor/loop_handler.py - 闭环测试处理
- [ ] report/builder.py - 报告生成
- [ ] trace/tracker.py - 追踪记录

### 测试脚本（入口点）
- [ ] test_single_case.py - 单个用例测试
- [ ] test_kol_loop.py - 闭环测试
- [ ] test_kol_complete.py - 完整测试

### 配置和文档
- [ ] config.py (示例版本，去掉敏感信息)
- [ ] requirements.txt - 依赖列表
- [ ] README.md - 使用说明

## 要排除的文件/目录
- [ ] traces/ - 运行产生的追踪日志
- [ ] screenshots/ - 运行产生的截图
- [ ] monitor_case21.py - 临时脚本
- [ ] __pycache__/ - Python缓存
- [ ] *.pyc - 编译文件
- [ ] .git/ - Git信息

## 需要创建的文件
- [ ] README.md - 使用说明
- [ ] requirements.txt - 依赖列表
- [ ] config.example.py - 配置示例
