from typing import Dict, Optional
import autogen

from a2sql.core.base_manager import BaseManager
from a2sql.utils import get_logger, log_method_execution_time

logger = get_logger(__name__)

class TaskManager(BaseManager):
    def __init__(self, llm_config: Optional[Dict] = None, prompt_templates: Optional[Dict[str, str]] = None):
        super().__init__()
        self.llm_config = llm_config
        self.prompt_templates = prompt_templates
        self.groupchat: Optional[autogen.GroupChat] = None
        self.manager: Optional[autogen.GroupChatManager] = None
    
    def initialize(self) -> None:
        if not self.prompt_templates or "task_prompt" not in self.prompt_templates:
            raise ValueError("TaskManager requires prompt_templates with 'task_prompt' field")
        self._initialized = True
    
    def validate(self) -> bool:
        return self._initialized
    
    @log_method_execution_time
    def create_groupchat(self, agents: list, max_round: int = 20, sql_exe: bool = True) -> autogen.GroupChat:
        logger.info(f"Creating GroupChat: agents={len(agents)}, max_round={max_round}, sql_exe={sql_exe}")
        # 测试环境：定义发言顺序
        # 生产环境：需要使用更为严谨的调度流程
        def custom_speaker_selection(last_speaker, groupchat):
            """自定义发言顺序 - 支持动态流程"""
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
                # 关键分支: 根据sql_exe决定是否执行
                if sql_exe:
                    # 执行SQL
                    return [a for a in groupchat.agents if "SQL_Executor" in a.name][0]
                else:
                    # 不执行,直接去 Refiner 做静态检查
                    refiner_agents = [a for a in groupchat.agents if "Refiner" in a.name]
                    if refiner_agents:
                        return refiner_agents[0]
                    else:
                        # 如果没有Refiner,直接去 ChatGenerator(如果有)
                        chat_agents = [a for a in groupchat.agents if "Chat_Generator" in a.name]
                        if chat_agents:
                            return chat_agents[0]
                        else:
                            return None  # 结束
            
            elif "SQL_Executor" in last_speaker.name:
                # 检查是否有错误
                if "ERROR:" in last_content or "错误" in last_content:
                    return [a for a in groupchat.agents if "Refiner" in a.name][0]
                else:
                    # 执行成功,检查是否有 Chat_Generator
                    chat_agents = [a for a in groupchat.agents if "Chat_Generator" in a.name]
                    if chat_agents:
                        return chat_agents[0]
                    else:
                        # 没有ChatGenerator,直接结束 (sql2generate场景)
                        return None
            
            elif "Refiner" in last_speaker.name:
                # Refiner 修正后,重新生成 SQL
                return [a for a in groupchat.agents if "SQL_Generator" in a.name][0]
            
            elif "Chat_Generator" in last_speaker.name:
                # ChatGenerator 完成后结束
                return None
            
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
        
        return self.groupchat
    
    def get_manager(self) -> Optional[autogen.GroupChatManager]:
        return self.manager
    
    @log_method_execution_time
    def execute_task(self, user_proxy, nl_query: str, state=None) -> str:
        try:
            initial_message = self.prompt_templates["task_prompt"].format(nl_query=nl_query)

            """
            核心work流程:

            Step 1: 用户代理发送初始消息
                - User_Proxy 将 initial_message 发送到 GroupChat

            Step 2: GroupChatManager 启动轮次循环
                - 循环逻辑：
                    1. 调用 custom_speaker_selection(last_speaker, groupchat) 选择下一个发言者
                    2. 下一 Agent 发言
                    3. 将 Agent 发言内容 append 到 groupchat.messages
                    4. 如果 Agent 需要调用工具（如 SQL_Executor）：
                        - 执行工具
                        - 将工具返回结果 append 到 messages
                    5. 如果 Refiner 被触发：
                        - 对 SQL 或结果进行修正
                        - 再次生成消息

            Step 3: 循环结束条件
                - 达到 max_round
                - 或最后一条消息包含 TERMINATE

            最终结果：
                - self.groupchat.messages 中保存整个对话历史，包括：
                    * 每个 Agent 的发言
                    * 工具调用结果
                    * Refiner 修正消息
                    * 错误信息（如有）
            """
            user_proxy.initiate_chat(
                self.manager,
                message=initial_message
            )

            # Extract result from last message and record to state
            if self.groupchat and self.groupchat.messages:
                messages_count = len(self.groupchat.messages)
                last_message = self.groupchat.messages[-1]
                result = last_message.get('content', 'Task completed')
                
                if state and state.current_step:
                    # 构建详细的对话历史
                    conversation_history = []
                    for i, msg in enumerate(self.groupchat.messages):
                        content = msg.get('content', '')
                        conversation_history.append({
                            "index": i,
                            "sender": msg.get('name', 'unknown'),
                            "content": content,
                            "content_length": len(content)
                        })
                    if not state.current_step.metadata:
                        state.current_step.metadata = {}
                    
                    state.current_step.metadata.update({
                        "messages_count": messages_count,
                        "conversation_history": conversation_history,
                        "final_result_preview": result
                    })
            # TODO 如果没有self.groupchat.messages 记录一下badcase
            else:
                result = "Task completed"
                if state and state.current_step:
                    if not state.current_step.metadata:
                        state.current_step.metadata = {}
                    state.current_step.metadata["warning"] = "未找到对话消息"
            
            return result
            
        except Exception as e:
            logger.error(f"Task execution error: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            if state:
                state.fail_current_step(f"{type(e).__name__}: {str(e)}")
            
            raise
