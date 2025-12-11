from typing import Dict, List, Optional
import autogen

from a2sql.core.base_manager import BaseManager
from a2sql.agents import (
    NLAnalystAgent,
    SQLGeneratorAgent,
    SQLExecutorAgent,
    RefinerAgent,
    UserProxyAgent
)
from a2sql.utils import get_logger, log_method_execution_time

logger = get_logger(__name__)

class AgentManager(BaseManager):
    def __init__(self, llm_config: Optional[Dict] = None, db_path: Optional[str] = None):
        super().__init__({"llm_config": llm_config, "db_path": db_path})
        self.agents: Dict[str, any] = {}
        self.autogen_agents: List[autogen.Agent] = []
    
    def initialize(self) -> None:
        llm_config = self.get_config("llm_config")
        db_path = self.get_config("db_path")
        self.agents = {
            "user_proxy": UserProxyAgent(),
            "nl_analyst": NLAnalystAgent(llm_config),
            "sql_generator": SQLGeneratorAgent(llm_config),
            "sql_executor": SQLExecutorAgent(llm_config, db_path),
            "refiner": RefinerAgent(llm_config)
        }
        
        self._initialized = True
    
    def validate(self) -> bool:
        return self._initialized and len(self.agents) > 0
    
    @log_method_execution_time
    def create_agents(self, schema_prompt: str) -> List[autogen.Agent]:
        """Create all AutoGen agents"""
        if not self.is_initialized():
            self.initialize()
        
        logger.info(f"Creating agents with schema length: {len(schema_prompt)}")
        
        self.autogen_agents = [
            self.agents["user_proxy"].create_agent(),
            self.agents["nl_analyst"].create_agent(schema=schema_prompt),
            self.agents["sql_generator"].create_agent(schema=schema_prompt),
            self.agents["sql_executor"].create_agent(),
            self.agents["refiner"].create_agent(schema=schema_prompt)
        ]
        
        agent_names = [agent.name for agent in self.autogen_agents]
        logger.info(f"Created {len(self.autogen_agents)} agents: {', '.join(agent_names)}")
        
        return self.autogen_agents
    
    def get_agent_by_name(self, name: str) -> Optional[any]:
        return self.agents.get(name)
    
    def get_all_agents(self) -> List[autogen.Agent]:
        return self.autogen_agents
