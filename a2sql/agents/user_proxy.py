"""
User Proxy Agent
用户代理
"""
import autogen
from typing import Dict, Any
from a2sql.template.user_proxy import PROMPT

class UserProxyAgent:
    def __init__(self, name: str = "User_Proxy"):
        self.name = name
        self._agent = None
    
    def create_agent(self) -> autogen.UserProxyAgent:
        self._agent = autogen.UserProxyAgent(
            name=self.name,
            human_input_mode="TERMINATE",
            max_consecutive_auto_reply=10,
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config=False,
            system_message=PROMPT
        )
        return self._agent
    
    def get_agent(self) -> autogen.UserProxyAgent:
        return self._agent
