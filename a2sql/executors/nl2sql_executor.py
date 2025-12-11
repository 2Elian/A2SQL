from typing import Dict, Optional, Any
import uuid

from a2sql.core.base_executor import BaseExecutor, ExecutionResult, ExecutionStatus
from a2sql.core.execution_state import ExecutionState, create_execution_state
from a2sql.managers import SchemaManager, AgentManager, TaskManager
from a2sql.utils import get_logger, log_method_execution_time
from a2sql.utils.error_logger import get_error_logger

logger = get_logger(__name__)
error_logger = get_error_logger()

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
        task_id = kwargs.get("task_id", str(uuid.uuid4()))
        state = create_execution_state(task_id, db_id, nl_query)
        
        logger.info(f"[{task_id}] 开始执行 NL2SQL: db_id={db_id}, query={nl_query[:50]}...")
        
        try:
            self._set_status(ExecutionStatus.RUNNING)
            
            # Step 1: Get and format schema
            step1 = state.start_step(
                "format_schema",
                "schema",
                "格式化数据库 Schema",
                {"db_id": db_id}
            )
            logger.info(f"[{task_id}] Step 1: 格式化数据库 Schema")
            
            schema_prompt = self.schema_manager.format_schema_for_prompt(db_id)
            
            state.complete_current_step({
                "schema_length": len(schema_prompt),
                "schema_preview": schema_prompt[:200] + "..."
            })
            logger.info(f"[{task_id}] Schema 格式化完成: {len(schema_prompt)} chars")
            
            # Step 2: Create agents
            step2 = state.start_step(
                "create_agents",
                "agent",
                "创建 Agent 团队",
                {"schema_length": len(schema_prompt)}
            )
            logger.info(f"[{task_id}] Step 2: 创建 Agent 团队")
            
            agents = self.agent_manager.create_agents(schema_prompt)
            agent_names = [a.name for a in agents]
            
            state.complete_current_step({
                "agents_count": len(agents),
                "agent_names": agent_names
            })
            logger.info(f"[{task_id}] 创建了 {len(agents)} 个 Agents: {', '.join(agent_names)}")
            
            # Step 3: Create group chat
            max_round = kwargs.get("max_round", 20)
            step3 = state.start_step(
                "create_groupchat",
                "agent",
                "创建群聊管理器",
                {"max_round": max_round, "agent_count": len(agents)}
            )
            logger.info(f"[{task_id}] Step 3: 创建群聊管理器")
            
            self.task_manager.create_groupchat(agents, max_round)
            
            state.complete_current_step({
                "max_round": max_round,
                "groupchat_created": True
            })
            logger.info(f"[{task_id}] GroupChat 创建完成: max_round={max_round}")
            
            # Step 4: Execute task
            step4 = state.start_step(
                "execute_agents",
                "execution",
                "Agent 协作执行 NL2SQL 任务",
                {"nl_query": nl_query}
            )
            logger.info(f"[{task_id}] Step 4: 执行 NL2SQL 任务")
            
            user_proxy = self.agent_manager.get_agent_by_name("user_proxy").get_agent()
            
            # 传递 state 给 task_manager
            result = self.task_manager.execute_task(
                user_proxy, 
                nl_query, 
                db_id,
                state=state  # 传递 state
            )
            
            state.complete_current_step({
                "result_length": len(str(result)),
                "result_preview": str(result)[:200] + "..."
            })
            logger.info(f"[{task_id}] 任务执行完成")
            
            self._set_status(ExecutionStatus.SUCCESS)
            state.complete(final_result=result)
            
            return ExecutionResult(
                status=ExecutionStatus.SUCCESS,
                data=result,
                metadata={
                    "task_id": task_id,
                    "db_id": db_id,
                    "nl_query": nl_query,
                    "schema_length": len(schema_prompt),
                    "agents_count": len(agents),
                    "max_round": max_round,
                    "execution_state": state.to_dict()  # 包含完整状态
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
