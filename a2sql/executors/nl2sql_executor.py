from typing import Dict, Optional, Any

from a2sql.core.base_executor import BaseExecutor, ExecutionResult, ExecutionStatus
from a2sql.managers import SchemaManager, AgentManager, TaskManager
from a2sql.utils import get_logger, log_method_execution_time

logger = get_logger(__name__)

class NL2SQLExecutor(BaseExecutor):
    def __init__(self, schema_file: str, llm_config: Optional[Dict] = None, db_path: Optional[str] = None):
        super().__init__({
            "schema_file": schema_file, 
            "llm_config": llm_config, 
            "db_path": db_path
        })
        self.llm_config = llm_config
        self.schema_manager = SchemaManager(schema_file)
        self.agent_manager = AgentManager(llm_config, db_path)
        self.task_manager = TaskManager(llm_config)

        self.schema_manager.initialize()
        self.agent_manager.initialize()
        self.task_manager.initialize()
    
    @log_method_execution_time
    def execute(self, db_id: str, nl_query: str, **kwargs) -> ExecutionResult:
        """Execute NL2SQL conversion task"""
        logger.info(f"Input: db_id={db_id}, query={nl_query[:50]}...")
        
        try:
            self._set_status(ExecutionStatus.RUNNING)
            
            # Step 1: Get and format schema
            logger.info("Step 1: Formatting database schema")
            schema_prompt = self.schema_manager.format_schema_for_prompt(db_id)
            logger.info(f"Schema formatted: {len(schema_prompt)} chars")
            
            # Step 2: Create agents
            logger.info("Step 2: Creating agent team")
            agents = self.agent_manager.create_agents(schema_prompt)
            logger.info(f"Created {len(agents)} agents")
            
            # Step 3: Create group chat
            logger.info("Step 3: Creating group chat")
            max_round = kwargs.get("max_round", 20)
            self.task_manager.create_groupchat(agents, max_round)
            logger.info(f"GroupChat created with max_round={max_round}")
            
            # Step 4: Execute task
            logger.info("Step 4: Executing NL2SQL task")
            user_proxy = self.agent_manager.get_agent_by_name("user_proxy").get_agent()
            result = self.task_manager.execute_task(user_proxy, nl_query, db_id)
            logger.info(f"Task completed successfully")
            
            self._set_status(ExecutionStatus.SUCCESS)
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                data=result,
                metadata={
                    "db_id": db_id,
                    "nl_query": nl_query,
                    "schema_length": len(schema_prompt),
                    "agents_count": len(agents),
                    "max_round": max_round
                }
            )
            
        except Exception as e:
            self._set_status(ExecutionStatus.FAILED)
            logger.error(f"Task failed: {type(e).__name__}: {str(e)}")
            
            import traceback
            logger.debug(f"Traceback: {traceback.format_exc()}")
            
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                error=str(e),
                metadata={
                    "db_id": db_id,
                    "nl_query": nl_query,
                    "error_type": type(e).__name__
                }
            )
    
    def get_available_databases(self) -> list:
        return self.schema_manager.get_all_db_ids()
    
    def get_schema_info(self, db_id: str) -> Optional[Dict]:
        return self.schema_manager.get_schema_by_id(db_id)
