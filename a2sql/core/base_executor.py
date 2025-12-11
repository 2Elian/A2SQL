from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from enum import Enum


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionResult:
    def __init__(
        self, 
        status: ExecutionStatus,
        data: Any = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.status = status
        self.data = data
        self.error = error
        self.metadata = metadata or {}
    
    def is_success(self) -> bool:
        return self.status == ExecutionStatus.SUCCESS
    
    def is_failed(self) -> bool:
        return self.status == ExecutionStatus.FAILED
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata
        }


class BaseExecutor(ABC):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._status = ExecutionStatus.PENDING
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> ExecutionResult:
        raise NotImplementedError
    
    def get_status(self) -> ExecutionStatus:
        return self._status
    
    def _set_status(self, status: ExecutionStatus) -> None:
        self._status = status
    
    def reset(self) -> None:
        self._status = ExecutionStatus.PENDING
