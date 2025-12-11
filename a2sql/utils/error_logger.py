import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class ErrorDataLogger:
    def __init__(self, log_file: str = "logs/error_data.log"):
        self.log_file = log_file
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        log_dir = os.path.dirname(self.log_file)
        if log_dir:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    def log_error(
        self,
        task_id: str,
        db_id: str,
        nl_query: str,
        error_type: str,
        error_message: str,
        failed_step: str,
        step_type: str,
        traceback: str = None,
        execution_state: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None
    ):
        """
        args:
            task_id: 任务ID
            db_id: 数据库ID
            nl_query: 自然语言查询
            error_type: 错误类型
            error_message: 错误信息
            failed_step: 失败的步骤名称
            step_type: 步骤类型 (schema/agent/execution/validation)
            traceback: 完整的错误堆栈
            execution_state: 执行状态详情
            metadata: 其他元数据
        """
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "db_id": db_id,
            "nl_query": nl_query,
            "error": {
                "type": error_type,
                "message": error_message,
                "failed_step": failed_step,
                "step_type": step_type,
                "traceback": traceback
            },
            "execution_state": execution_state or {},
            "metadata": metadata or {}
        }
        
        # 写入日志文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(error_record, ensure_ascii=False) + '\n')
    
    def log_from_state(self, state, error_type: str, error_message: str, traceback: str = None):
        """
        args:
            state: ExecutionState 对象
            error_type: 错误类型
            error_message: 错误信息
            traceback: 错误堆栈
        """
        # 找到失败的步骤
        failed_step = None
        step_type = None
        
        if state.current_step:
            failed_step = state.current_step.step_name
            step_type = state.current_step.step_type
        else:
            # 从步骤列表中找最后一个失败的
            for step in reversed(state.steps):
                if step.status.value == 'failed':
                    failed_step = step.step_name
                    step_type = step.step_type
                    break
        
        if not failed_step:
            failed_step = "unknown"
            step_type = "unknown"
        
        self.log_error(
            task_id=state.task_id,
            db_id=state.db_id,
            nl_query=state.nl_query,
            error_type=error_type,
            error_message=error_message,
            failed_step=failed_step,
            step_type=step_type,
            traceback=traceback,
            execution_state=state.to_dict(),
            metadata=state.metadata
        )


# 全局错误记录器实例
_error_logger = ErrorDataLogger()


def get_error_logger() -> ErrorDataLogger:
    """获取错误记录器实例"""
    return _error_logger


def log_badcase(
    task_id: str,
    db_id: str,
    nl_query: str,
    error_type: str,
    error_message: str,
    failed_step: str = "unknown",
    step_type: str = "unknown",
    traceback: str = None,
    **kwargs
):
    """
    快捷方法:记录 badcase
    
    Args:
        task_id: 任务ID
        db_id: 数据库ID
        nl_query: 自然语言查询
        error_type: 错误类型
        error_message: 错误信息
        failed_step: 失败步骤
        step_type: 步骤类型
        traceback: 错误堆栈
        **kwargs: 其他元数据
    """
    _error_logger.log_error(
        task_id=task_id,
        db_id=db_id,
        nl_query=nl_query,
        error_type=error_type,
        error_message=error_message,
        failed_step=failed_step,
        step_type=step_type,
        traceback=traceback,
        metadata=kwargs
    )
