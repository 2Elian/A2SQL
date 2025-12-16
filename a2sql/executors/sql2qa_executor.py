from typing import Dict, Optional, Any
import uuid

from a2sql.core.base_executor import BaseExecutor, ExecutionResult, ExecutionStatus
from a2sql.core.execution_state import ExecutionState, create_execution_state
from a2sql.managers import SchemaManager, AgentManager, TaskManager
from a2sql.utils import get_logger, log_method_execution_time
from a2sql.utils.error_logger import get_error_logger
from a2sql.template import SQL2QA

logger = get_logger(__name__)
error_logger = get_error_logger()

class SQL2QaExecutor(BaseExecutor):
    def __init__(
        self,
        schema_file: str,
        llm_config: Optional[Dict] = None,
        db_config: Optional[Dict] = None,
        prompt_templates: Optional[Dict[str, str]] = None
    ):
        super().__init__({"schema_file": schema_file,"llm_config": llm_config,"db_config": db_config,"prompt_templates": prompt_templates})
        self.llm_config = llm_config
        prompt_templates = SQL2QA
        self.schema_manager = SchemaManager(schema_file)
        self.agent_manager = AgentManager(llm_config,  db_config=db_config,  prompt_templates=prompt_templates,  include_chat_generator=True, sql_exe=True)
        self.task_manager = TaskManager(llm_config, prompt_templates)

        self.schema_manager.initialize()
        self.agent_manager.initialize()
        self.task_manager.initialize()
    
    @log_method_execution_time
    def execute(self, db_id: str, nl_query: str, **kwargs) -> ExecutionResult:
        """Execute NL2QA conversion task - sql_exe is always True"""
        task_id = kwargs.get("task_id", str(uuid.uuid4()))
        state = create_execution_state(task_id, db_id, nl_query)
        try:
            self._set_status(ExecutionStatus.RUNNING)
            
            # Step 1: Get and format schema
            step1 = state.start_step(
                "format_schema",
                "schema",
                "Formatting database schema",
                {"db_id": db_id}
            )
            schema_prompt = self.schema_manager.format_schema_for_prompt(db_id)
            
            state.complete_current_step({
                "schema_length": len(schema_prompt),
                "schema_preview": schema_prompt
            })
            
            # Step 2: Create agents
            step2 = state.start_step(
                "create_agents",
                "agent",
                "Create an Agent Team",
                {"schema_length": len(schema_prompt)}
            )
            agents = self.agent_manager.create_agents(schema_prompt)
            agent_names = [a.name for a in agents]
            
            state.complete_current_step({
                "agents_count": len(agents),
                "agent_names": agent_names
            })

            # Step 3: Create group chat
            max_round = kwargs.get("max_round", 20)
            step3 = state.start_step(
                "create_groupchat",
                "agent",
                "Create a group chat manager",
                {"max_round": max_round, "agent_count": len(agents)}
            )
            
            self.task_manager.create_groupchat(agents, max_round)
            state.complete_current_step({
                "max_round": max_round,
                "groupchat_created": True
            })
            
            # Step 4: Execute task
            step4 = state.start_step(
                "execute_agents",
                "execution",
                "Agents collaborate to execute NL2QA tasks",
                {"nl_query": nl_query, "sql_exe": True}
            )
            user_proxy = self.agent_manager.get_agent_by_name("user_proxy").get_agent()
            result = self.task_manager.execute_task(user_proxy, nl_query, state=state)
            
            state.complete_current_step({
                "result_length": len(str(result)),
                "result_preview": str(result)
            })
            
            self._set_status(ExecutionStatus.SUCCESS)
            state.complete(final_result=result)
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                data=result,
                metadata={
                    "task_id": task_id,
                    "db_id": db_id,
                    "nl_query": nl_query,
                    "sql_exe": True,
                    "schema_length": len(schema_prompt),
                    "agents_count": len(agents),
                    "max_round": max_round,
                    "execution_state": state.to_dict()
                }
            )
            
        except Exception as e:
            self._set_status(ExecutionStatus.FAILED)
            error_msg = f"{type(e).__name__}: {str(e)}"
            logger.error(f"[{task_id}] 任务失败: {error_msg}")
            
            import traceback
            traceback_str = traceback.format_exc()
            logger.debug(f"[{task_id}] Traceback: {traceback_str}")
            
            state.fail(error_msg)
            
            # 记录 badcase 到 error_data.log
            error_logger.log_from_state(
                state=state,
                error_type=type(e).__name__,
                error_message=str(e),
                traceback=traceback_str
            )
            logger.info(f"[{task_id}] Badcase 已记录到 logs/error_data.log")
            
            return ExecutionResult(
                status=ExecutionStatus.FAILED,
                error=error_msg,
                metadata={
                    "task_id": task_id,
                    "db_id": db_id,
                    "nl_query": nl_query,
                    "error_type": type(e).__name__,
                    "traceback": traceback_str,
                    "execution_state": state.to_dict()
                }
            )
    
    def get_available_databases(self) -> list:
        return self.schema_manager.get_all_db_ids()
    
    def get_schema_info(self, db_id: str) -> Optional[Dict]:
        return self.schema_manager.get_schema_by_id(db_id)
