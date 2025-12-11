import logging
import time
import functools
from typing import Callable, Any

_logger = None


def get_logger(name: str = "nl2sql") -> logging.Logger:
    """获取全局 logger 实例"""
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
    return _logger


def log_execution_time(func: Callable) -> Callable:
    """
    装饰器：记录函数执行时间
    
    使用方法:
        @log_execution_time
        def my_function():
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        logger = get_logger()
        func_name = f"{func.__module__}.{func.__qualname__}"
        
        logger.info(f"START: {func_name}")
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"END: {func_name} (elapsed: {elapsed:.3f}s)")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"FAILED: {func_name} (elapsed: {elapsed:.3f}s, error: {str(e)})")
            raise
    
    return wrapper


def log_method_execution_time(func: Callable) -> Callable:
    """
    装饰器：记录类方法执行时间
    
    使用方法:
        class MyClass:
            @log_method_execution_time
            def my_method(self):
                pass
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs) -> Any:
        logger = get_logger()
        class_name = self.__class__.__name__
        func_name = f"{class_name}.{func.__name__}"
        
        logger.info(f"START: {func_name}")
        start_time = time.time()
        
        try:
            result = func(self, *args, **kwargs)
            elapsed = time.time() - start_time
            logger.info(f"END: {func_name} (elapsed: {elapsed:.3f}s)")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"FAILED: {func_name} (elapsed: {elapsed:.3f}s, error: {str(e)})")
            raise
    
    return wrapper
