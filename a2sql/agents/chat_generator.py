from typing import Dict, Any
from a2sql.core.base_agent import BaseAgent


class ChatGeneratorAgent(BaseAgent):
    def __init__(self, llm_config: Dict[str, Any] = None, prompt_template: str = None):
        super().__init__("Chat_Generator", llm_config)
        self.prompt_template = prompt_template
    
    def _get_system_message(self, **kwargs) -> str:
        if not self.prompt_template:
            raise ValueError("ChatGeneratorAgent requires prompt_template")
        return self.prompt_template
    
    def _get_agent_config(self) -> Dict[str, Any]:
        return {
            "human_input_mode": "NEVER",
            "max_consecutive_auto_reply": 3,
        }
