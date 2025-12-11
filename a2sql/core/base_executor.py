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
        """是否执行成功"""
        return self.status == ExecutionStatus.SUCCESS
    
    def is_failed(self) -> bool:
        """是否执行失败"""
        return self.status == ExecutionStatus.FAILED
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata
        }


class BaseExecutor(ABC):
    """Executor 基类"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化执行器
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self._status = ExecutionStatus.PENDING
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> ExecutionResult:
        """
        执行任务(子类必须实现)
        
        Returns:
            执行结果
        """
        raise NotImplementedError
    
    def get_status(self) -> ExecutionStatus:
        """
        获取执行状态
        
        Returns:
            执行状态
        """
        return self._status
    
    def _set_status(self, status: ExecutionStatus) -> None:
        """
        设置执行状态
        
        Args:
            status: 执行状态
        """
        self._status = status
    
    def reset(self) -> None:
        """重置执行器状态"""
        self._status = ExecutionStatus.PENDING
