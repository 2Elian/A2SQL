from typing import Dict, List, Optional
import autogen

from a2sql.core.base_manager import BaseManager
from a2sql.agents import (
    NLAnalystAgent,
    SQLGeneratorAgent,
    SQLExecutorAgent,
    RefinerAgent,
    UserProxyAgent,
    ChatGeneratorAgent
)
from a2sql.utils import get_logger, log_method_execution_time

logger = get_logger(__name__)

class AgentManager(BaseManager):
    def __init__(self, llm_config: Optional[Dict] = None, db_config: Optional[Dict] = None,
        prompt_templates: Optional[Dict[str, str]] = None,
        include_chat_generator: bool = False, sql_exe: bool = True):
        super().__init__({
            "llm_config": llm_config,
            "db_path": db_config.get("database", None) if db_config is not None else None,
            "db_config": db_config,
            "prompt_templates": prompt_templates,
            "include_chat_generator": include_chat_generator,
            "sql_exe": sql_exe
        })
        self.agents: Dict[str, any] = {}
        self.autogen_agents: List[autogen.Agent] = []
    
    def initialize(self) -> None:
        llm_config = self.get_config("llm_config")
        db_path = self.get_config("db_path")
        db_config = self.get_config("db_config")
        prompt_templates = self.get_config("prompt_templates")
        include_chat_generator = self.get_config("include_chat_generator", False)
        sql_exe = self.get_config("sql_exe", True)
        
        if not prompt_templates:
            raise ValueError("AgentManager requires prompt_templates configuration")
        required_templates = ["user_proxy", "nl_analyst", "sql_generator"]
        if sql_exe:
            required_templates.append("sql_executor")
            required_templates.append("refiner")
        if include_chat_generator:
            required_templates.append("chat_generator")
        
        for template_name in required_templates:
            if template_name not in prompt_templates:
                raise ValueError(f"Missing required prompt template: {template_name}")
        final_db_config = db_config if db_config else ({"db_path": db_path, "db_type": "sqlite"} if db_path else None)
        self.agents = {
            "user_proxy": UserProxyAgent(
                prompt_template=prompt_templates["user_proxy"]
            ),
            "nl_analyst": NLAnalystAgent(
                llm_config=llm_config,
                prompt_template=prompt_templates["nl_analyst"]
            ),
            "sql_generator": SQLGeneratorAgent(
                llm_config=llm_config,
                prompt_template=prompt_templates["sql_generator"]
            )
        }
        if sql_exe:
            self.agents["sql_executor"] = SQLExecutorAgent(
                llm_config=llm_config,
                db_path=db_path if not final_db_config else None,
                db_config=final_db_config,
                prompt_template=prompt_templates["sql_executor"]
            )
            self.agents["refiner"] = RefinerAgent(
                llm_config=llm_config,
                prompt_template=prompt_templates["refiner"]
            )
        if include_chat_generator:
            self.agents["chat_generator"] = ChatGeneratorAgent(
                llm_config=llm_config,
                prompt_template=prompt_templates["chat_generator"]
            )
        
        self._initialized = True
    
    def validate(self) -> bool:
        return self._initialized and len(self.agents) > 0
    
    @log_method_execution_time
    def create_agents(self, schema_prompt: str, include_chat_generator: bool = None) -> List[autogen.Agent]:
        """
        Create all AutoGen agents
        
        Args:
            schema_prompt: Schema提示词
            include_chat_generator: 是否包含ChatGenerator,默认使用初始化时的设置
        """
        if not self.is_initialized():
            self.initialize()
        if include_chat_generator is None:
            include_chat_generator = self.get_config("include_chat_generator", False)
        self.autogen_agents = [
            self.agents["user_proxy"].create_agent(),
            self.agents["nl_analyst"].create_agent(schema=schema_prompt),
            self.agents["sql_generator"].create_agent(schema=schema_prompt),
        ]
        if "sql_executor" in self.agents:
            self.autogen_agents.append(
                self.agents["sql_executor"].create_agent()
            )
            self.autogen_agents.append(
                self.agents["refiner"].create_agent(schema=schema_prompt)
            )
        if include_chat_generator and "chat_generator" in self.agents:
            self.autogen_agents.append(
                self.agents["chat_generator"].create_agent()
            )
        
        agent_names = [agent.name for agent in self.autogen_agents]
        logger.info(f"Created {len(self.autogen_agents)} agents: {', '.join(agent_names)}")
        
        return self.autogen_agents
    
    def get_agent_by_name(self, name: str) -> Optional[any]:
        return self.agents.get(name)
    
    def get_all_agents(self) -> List[autogen.Agent]:
        return self.autogen_agents
