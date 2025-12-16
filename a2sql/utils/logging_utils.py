import logging
import time
import functools
import sys
from typing import Callable, Any

_logger = None
_configured_loggers = set()


def get_logger(name: str = "nl2sql") -> logging.Logger:
    global _configured_loggers
    
    logger = logging.getLogger(name)
    if name not in _configured_loggers:
        logger.setLevel(logging.INFO)
        
        # 避免重复添加 handler
        if not logger.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        _configured_loggers.add(name)
    
    return logger


def log_execution_time(func: Callable) -> Callable:
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
