import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class OperationTracker:
    """操作追踪系统 - 记录每个操作的链路和状态变化"""

    def __init__(self, case_id: str, description: str):
        self.case_id = case_id
        self.description = description
        self.trace_id = f"{case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.start_time = datetime.now()
        self.steps: List[Dict[str, Any]] = []
        self.before_state: Dict[str, Any] = {}
        self.after_state: Dict[str, Any] = {}
        self.result = "pending"
        self.error_msg = ""

    def record_step(self, action: str, target: str, status: str, details: Optional[Dict] = None):
        """记录一个操作步骤"""
        step = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "target": target,
            "status": status,
            "details": details or {}
        }
        self.steps.append(step)

    def set_before_state(self, state: Dict[str, Any]):
        """记录操作前的状态"""
        self.before_state = state

    def set_after_state(self, state: Dict[str, Any]):
        """记录操作后的状态"""
        self.after_state = state

    def set_result(self, result: str, error_msg: str = ""):
        """设置最终结果"""
        self.result = result
        self.error_msg = error_msg

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "trace_id": self.trace_id,
            "case_id": self.case_id,
            "description": self.description,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.now().isoformat(),
            "duration": (datetime.now() - self.start_time).total_seconds(),
            "steps": self.steps,
            "before_state": self.before_state,
            "after_state": self.after_state,
            "result": self.result,
            "error_msg": self.error_msg
        }

    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def save_to_file(self, output_dir: Optional[Path] = None) -> Path:
        """保存追踪日志到文件"""
        if output_dir is None:
            output_dir = Path(__file__).parent.parent / "traces"

        output_dir.mkdir(parents=True, exist_ok=True)

        file_path = output_dir / f"{self.trace_id}.json"
        file_path.write_text(self.to_json(), encoding="utf-8")

        return file_path


class TraceManager:
    """追踪管理器 - 管理所有操作的追踪日志"""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path(__file__).parent.parent / "traces"
        self.traces: Dict[str, OperationTracker] = {}

    def create_tracker(self, case_id: str, description: str) -> OperationTracker:
        """创建一个新的追踪器"""
        tracker = OperationTracker(case_id, description)
        self.traces[tracker.trace_id] = tracker
        return tracker

    def get_all_traces(self) -> List[Dict[str, Any]]:
        """获取所有追踪日志"""
        return [tracker.to_dict() for tracker in self.traces.values()]

    def save_all(self) -> List[Path]:
        """保存所有追踪日志"""
        paths = []
        for tracker in self.traces.values():
            path = tracker.save_to_file(self.output_dir)
            paths.append(path)
        return paths

    def get_trace_summary(self) -> Dict[str, Any]:
        """获取追踪摘要"""
        traces = self.get_all_traces()

        success_count = sum(1 for t in traces if t["result"] == "success")
        failed_count = sum(1 for t in traces if t["result"] == "failed")
        pending_count = sum(1 for t in traces if t["result"] == "pending")

        return {
            "total": len(traces),
            "success": success_count,
            "failed": failed_count,
            "pending": pending_count,
            "traces": traces
        }


# 全局追踪管理器
_trace_manager = TraceManager()


def get_trace_manager() -> TraceManager:
    """获取全局追踪管理器"""
    return _trace_manager
