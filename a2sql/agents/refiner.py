"""
Refiner Agent
SQL 错误修正专家
"""
from typing import Dict, Any
from a2sql.core.base_agent import BaseAgent
from a2sql.template.refiner import PROMPT


class RefinerAgent(BaseAgent):
    def __init__(self, llm_config: Dict[str, Any] = None):
        super().__init__("Refiner", llm_config)
    
    def _get_system_message(self, **kwargs) -> str:
        schema = kwargs.get("schema", "")
        return PROMPT.format(schema=schema)
    
    def _get_agent_config(self) -> Dict[str, Any]:
        return {
            "human_input_mode": "NEVER",
            "max_consecutive_auto_reply": 3,
        }
