from abc import ABC, abstractmethod
import os
from typing import Dict, Any, Optional
import autogen


class BaseAgent(ABC):
    def __init__(self, name: str, llm_config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.llm_config = llm_config or self._get_default_llm_config()
        self._agent = None
    
    @abstractmethod
    def _get_system_message(self, **kwargs) -> str:
        raise NotImplementedError
    
    @abstractmethod
    def _get_agent_config(self) -> Dict[str, Any]:
        raise NotImplementedError
    
    def _get_default_llm_config(self) -> Dict[str, Any]:
        return {
            "config_list": [
                {
                    "model": os.getenv("MODEL_NAME", "gpt-4"),
                    "api_key": os.getenv("OPENAI_API_KEY"),
                }
            ]
        }
    
    def create_agent(self, **kwargs) -> autogen.AssistantAgent:
        system_message = self._get_system_message(**kwargs)
        config = self._get_agent_config()
        
        self._agent = autogen.AssistantAgent(
            name=self.name,
            llm_config=self.llm_config,
            system_message=system_message,
            **config
        )
        
        return self._agent
    
    def get_agent(self) -> Optional[autogen.AssistantAgent]:
        return self._agent
    
    @property
    def agent_name(self) -> str:
        return self.name
