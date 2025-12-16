import autogen
from typing import Dict, Any

class UserProxyAgent:
    def __init__(self, name: str = "User_Proxy", prompt_template: str = None):
        self.name = name
        self._agent = None
        self.prompt_template = prompt_template
    
    def create_agent(self) -> autogen.UserProxyAgent:
        if not self.prompt_template:
            raise ValueError("UserProxyAgent requires prompt_template")
        
        self._agent = autogen.UserProxyAgent(
            name=self.name,
            human_input_mode="TERMINATE",
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config=False,
            system_message=self.prompt_template
        )
        return self._agent
    
    def get_agent(self) -> autogen.UserProxyAgent:
        return self._agent
