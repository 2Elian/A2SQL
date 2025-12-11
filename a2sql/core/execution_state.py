from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import json


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class ExecutionStep:
    def __init__(
        self,
        step_name: str,
        step_type: str,
        description: str = ""
    ):
        self.step_name = step_name
        self.step_type = step_type  # schema/agent/execution/validation
        self.description = description
        self.status = StepStatus.PENDING
        self.input_data: Optional[Dict[str, Any]] = None
        self.output_data: Optional[Dict[str, Any]] = None
        self.error: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.duration: Optional[float] = None
        self.agent_name: Optional[str] = None
        self.metadata: Dict[str, Any] = {}
    
    def start(self, input_data: Dict[str, Any] = None):
        self.status = StepStatus.RUNNING
        self.start_time = datetime.now()
        self.input_data = input_data or {}
    
    def complete(self, output_data: Dict[str, Any] = None):
        self.status = StepStatus.SUCCESS
        self.end_time = datetime.now()
        self.output_data = output_data or {}
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
    
    def fail(self, error: str):
        self.status = StepStatus.FAILED
        self.end_time = datetime.now()
        self.error = error
        if self.start_time:
            self.duration = (self.end_time - self.start_time).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_name": self.step_name,
            "step_type": self.step_type,
            "description": self.description,
            "status": self.status.value,
            "agent_name": self.agent_name,
            "input_data": self.input_data,
            "output_data": self.output_data,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.duration,
            "metadata": self.metadata
        }


class ExecutionState:
    def __init__(self, task_id: str, db_id: str, nl_query: str):
        self.task_id = task_id
        self.db_id = db_id
        self.nl_query = nl_query
        self.steps: List[ExecutionStep] = []
        self.current_step: Optional[ExecutionStep] = None
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.overall_status = StepStatus.PENDING
        self.final_sql: Optional[str] = None
        self.final_result: Optional[Any] = None
        self.metadata: Dict[str, Any] = {
            "db_id": db_id,
            "nl_query": nl_query,
            "task_id": task_id
        }
    
    def add_step(
        self,
        step_name: str,
        step_type: str,
        description: str = "",
        agent_name: str = None
    ) -> ExecutionStep:
        step = ExecutionStep(step_name, step_type, description)
        if agent_name:
            step.agent_name = agent_name
        self.steps.append(step)
        self.current_step = step
        return step
    
    def start_step(
        self,
        step_name: str,
        step_type: str,
        description: str = "",
        input_data: Dict[str, Any] = None,
        agent_name: str = None
    ) -> ExecutionStep:
        step = self.add_step(step_name, step_type, description, agent_name)
        step.start(input_data)
        return step
    
    def complete_current_step(self, output_data: Dict[str, Any] = None):
        if self.current_step:
            self.current_step.complete(output_data)
    
    def fail_current_step(self, error: str):
        if self.current_step:
            self.current_step.fail(error)
    
    def complete(self, final_sql: str = None, final_result: Any = None):
        self.overall_status = StepStatus.SUCCESS
        self.end_time = datetime.now()
        self.final_sql = final_sql
        self.final_result = final_result
    
    def fail(self, error: str):
        self.overall_status = StepStatus.FAILED
        self.end_time = datetime.now()
        if self.current_step and self.current_step.status == StepStatus.RUNNING:
            self.current_step.fail(error)
    
    def get_duration(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.overall_status.value,
            "total_steps": len(self.steps),
            "successful_steps": sum(1 for s in self.steps if s.status == StepStatus.SUCCESS),
            "failed_steps": sum(1 for s in self.steps if s.status == StepStatus.FAILED),
            "duration": self.get_duration(),
            "final_sql": self.final_sql,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "db_id": self.db_id,
            "nl_query": self.nl_query,
            "overall_status": self.overall_status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration": self.get_duration(),
            "steps": [step.to_dict() for step in self.steps],
            "final_sql": self.final_sql,
            "final_result": self.final_result,
            "summary": self.get_summary(),
            "metadata": self.metadata
        }
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


# TODO 全局状态存储(生产环境需改为Redis)
_execution_states: Dict[str, ExecutionState] = {}


def create_execution_state(task_id: str, db_id: str, nl_query: str) -> ExecutionState:
    state = ExecutionState(task_id, db_id, nl_query)
    _execution_states[task_id] = state
    return state


def get_execution_state(task_id: str) -> Optional[ExecutionState]:
    return _execution_states.get(task_id)


def remove_execution_state(task_id: str):
    if task_id in _execution_states:
        del _execution_states[task_id]
