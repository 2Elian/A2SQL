from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseManager(ABC):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialized = False
    
    @abstractmethod
    def initialize(self) -> None:
        raise NotImplementedError
    
    @abstractmethod
    def validate(self) -> bool:
        raise NotImplementedError
    
    def is_initialized(self) -> bool:
        return self._initialized
    
    def get_config(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        self.config[key] = value
