"""
闭环测试工作流模块

提供通用的闭环测试工作流，支持所有类型的闭环测试。
"""

from .loop_monitor import LoopMonitor
from .loop_reporter import LoopReporter

__all__ = ['LoopMonitor', 'LoopReporter']
