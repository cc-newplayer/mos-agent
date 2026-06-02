# 闭环测试工作流 - 多系统支持方案

## 概述

当前工作流针对 MOS 系统设计。如果需要支持其他系统（闭环逻辑相同，但网页布局不同），可以通过**系统适配器模式**实现。

## 适配难度评估

**难度：⭐⭐ 中等**

- 核心逻辑（轮询、监控、报告）**完全不变**
- 只需适配 **20-30 行代码**
- 改动集中在**选择器和信号检查**

## 需要适配的部分

### 1. 页面导航 URL
```python
# MOS 系统
dialog_page_url = "/decision"

# 其他系统
dialog_page_url = "/chat"  # 示例
```

### 2. 对话卡片选择器
```python
# MOS 系统
# 查找包含"引流号"的卡片
const cards = Array.from(document.querySelectorAll('*')).filter(el => {
    const text = el.textContent;
    return text && text.includes('引流号') && text.length < 150;
});

# 其他系统
# 可能需要改为：
const cards = document.querySelectorAll('.dialog-card');
// 或其他选择器
```

### 3. 完成信号检查
```python
# MOS 系统
completion_signals = [
    "MarketingAI任务执行报告",
    "规划阶段出错",
    "Error code: 500",
    "报告生成失败"
]

# 其他系统
completion_signals = [
    "Task completed",  # 示例
    "Error occurred",
    "Report generated"
]
```

## 推荐的实现方案

### 方案：系统适配器模式

创建 `system_adapters.py`：

```python
class SystemAdapter:
    """系统适配器基类"""
    
    def get_dialog_page_url(self):
        """获取对话页面URL"""
        raise NotImplementedError
    
    def get_card_selector_js(self):
        """获取卡片选择器 JavaScript 代码"""
        raise NotImplementedError
    
    def get_completion_signals(self):
        """获取完成信号列表"""
        raise NotImplementedError
    
    def check_completion(self, content):
        """检查是否完成"""
        for signal in self.get_completion_signals():
            if signal in content:
                return True
        return False


class MOSAdapter(SystemAdapter):
    """MOS 系统适配器"""
    
    def get_dialog_page_url(self):
        return "/decision"
    
    def get_card_selector_js(self):
        return '''() => {
            const cards = Array.from(document.querySelectorAll('*')).filter(el => {
                const text = el.textContent;
                return text && text.includes('引流号') && text.length < 150;
            });
            if (cards.length > 0) {
                cards[0].click();
            }
        }'''
    
    def get_completion_signals(self):
        return [
            "MarketingAI任务执行报告",
            "规划阶段出错",
            "Error code: 500",
            "报告生成失败"
        ]


class OtherSystemAdapter(SystemAdapter):
    """其他系统适配器 - 示例"""
    
    def get_dialog_page_url(self):
        return "/chat"
    
    def get_card_selector_js(self):
        return '''() => {
            const cards = document.querySelectorAll('.dialog-card');
            if (cards.length > 0) {
                cards[0].click();
            }
        }'''
    
    def get_completion_signals(self):
        return [
            "Task completed",
            "Report generated",
            "Error occurred"
        ]
```

### 修改工作流使用适配器

在 `test_loop_workflow.py` 中：

```python
from system_adapters import MOSAdapter, OtherSystemAdapter

# 选择系统
adapter = MOSAdapter()  # 或 OtherSystemAdapter()

# 在监控中使用
monitor = LoopMonitor(SYSTEM_URL, adapter=adapter)
```

## 实现步骤

1. **创建适配器文件** `system_adapters.py`
2. **修改 `loop_monitor.py`** 接收适配器参数
3. **修改 `test_loop_workflow.py`** 传入适配器
4. **为新系统创建适配器类**
5. **测试新系统**

## 预期工作量

- 创建基础适配器：**30 分钟**
- 为新系统创建适配器：**15-30 分钟**（取决于系统复杂度）
- 测试：**30 分钟**

## 优势

✅ 核心逻辑不变
✅ 易于扩展
✅ 易于维护
✅ 支持多系统
✅ 代码复用率高

## 何时实现

当需要支持新系统时，按照上述方案实现即可。目前先专注于 MOS 系统的完善。
