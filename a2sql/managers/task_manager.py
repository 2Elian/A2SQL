from typing import Dict, Optional
import autogen

from a2sql.core.base_manager import BaseManager
from a2sql.template.task_prompt import PROMPT
from a2sql.utils import get_logger, log_method_execution_time

logger = get_logger(__name__)


class TaskManager(BaseManager):
    def __init__(self, llm_config: Optional[Dict] = None):
        super().__init__()
        self.llm_config = llm_config
        self.groupchat: Optional[autogen.GroupChat] = None
        self.manager: Optional[autogen.GroupChatManager] = None
    
    def initialize(self) -> None:
        self._initialized = True
    
    def validate(self) -> bool:
        return self._initialized
    
    @log_method_execution_time
    def create_groupchat(
        self, 
        agents: list,
        max_round: int = 20
    ) -> autogen.GroupChat:
        """Create group chat"""
        logger.info(f"Creating GroupChat: agents={len(agents)}, max_round={max_round}")
        
        # 测试环境：定义发言顺序: User_Proxy -> NL_Analyst -> SQL_Generator -> SQL_Executor -> (Refiner if error) -> User_Proxy
        # 生产环境：需要使用一个LLM来调度
        def custom_speaker_selection(last_speaker, groupchat):
            messages = groupchat.messages
            if len(messages) <= 1:
                # 第一轮: User_Proxy 发言后,NL_Analyst 分析
                return [a for a in groupchat.agents if "NL_Analyst" in a.name][0]
            
            last_message = messages[-1] if messages else {}
            last_content = last_message.get('content', '')
            
            # 如果包含 TERMINATE,结束对话
            if 'TERMINATE' in last_content:
                return None
            
            # 根据上一个发言者确定下一个发言者
            if "NL_Analyst" in last_speaker.name:
                return [a for a in groupchat.agents if "SQL_Generator" in a.name][0]
            elif "SQL_Generator" in last_speaker.name:
                return [a for a in groupchat.agents if "SQL_Executor" in a.name][0]
            elif "SQL_Executor" in last_speaker.name:
                # 检查是否有错误
                if "错误" in last_content or "error" in last_content.lower():
                    return [a for a in groupchat.agents if "Refiner" in a.name][0]
                else:
                    # 成功则返回 User_Proxy 结束
                    return [a for a in groupchat.agents if "User_Proxy" in a.name][0]
            elif "Refiner" in last_speaker.name:
                # Refiner 修正后,重新生成 SQL
                return [a for a in groupchat.agents if "SQL_Generator" in a.name][0]
            else:
                # 默认返回 NL_Analyst
                return [a for a in groupchat.agents if "NL_Analyst" in a.name][0]
        
        self.groupchat = autogen.GroupChat(
            agents=agents,
            messages=[],
            max_round=max_round,
            speaker_selection_method=custom_speaker_selection  # 使用自定义发言者选择
        )
        
        self.manager = autogen.GroupChatManager(
            groupchat=self.groupchat,
            llm_config=self.llm_config
        )
        
        logger.info("GroupChatManager created with custom speaker selection")
        
        return self.groupchat
    
    def get_manager(self) -> Optional[autogen.GroupChatManager]:
        """获取群聊管理器"""
        return self.manager
    
    @log_method_execution_time
    def execute_task(
        self,
        user_proxy,
        nl_query: str,
        db_id: str,
        state=None 
    ) -> str:
        """Execute task"""
        logger.info(f"Executing task: db={db_id}, query={nl_query[:50]}...")
        
        try:
            initial_message = PROMPT.format(nl_query=nl_query)
            logger.info("开始 Agent 协作对话")
            if state:
                state.start_step(
                    "agent_conversation",
                    "execution",
                    "Agent 协作对话",
                    {"initial_message": initial_message[:100] + "..."}
                )
            
            user_proxy.initiate_chat(
                self.manager,
                message=initial_message
            )
            
            logger.info("Agent 对话完成")
            
            # Extract result from last message
            if self.groupchat and self.groupchat.messages:
                messages_count = len(self.groupchat.messages)
                last_message = self.groupchat.messages[-1]
                result = last_message.get('content', 'Task completed')
                
                logger.info(f"从 {messages_count} 条消息中提取结果")
                
                # 记录 Agent 对话历史
                if state:
                    conversation_history = []
                    for i, msg in enumerate(self.groupchat.messages):
                        conversation_history.append({
                            "index": i,
                            "sender": msg.get('name', 'unknown'),
                            "content_preview": msg.get('content', '')[:200] + "...",
                            "content_length": len(msg.get('content', ''))
                        })
                    
                    state.complete_current_step({
                        "messages_count": messages_count,
                        "conversation_history": conversation_history,
                        "final_result_preview": result[:200] + "..."
                    })
            else:
                result = "Task completed"
                logger.warning("未找到对话消息")
                
                if state:
                    state.complete_current_step({
                        "messages_count": 0,
                        "warning": "未找到对话消息"
                    })
            
            logger.info(f"任务结果: {str(result)[:100]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"Task execution error: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            if state:
                state.fail_current_step(f"{type(e).__name__}: {str(e)}")
            
            raise
