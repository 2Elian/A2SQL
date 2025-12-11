import autogen
import sqlite3
from typing import Dict, Any

from a2sql.core.base_agent import BaseAgent
from a2sql.template.sql_executor import PROMPT



class SQLExecutorAgent(BaseAgent):
    def __init__(self, llm_config: Dict[str, Any] = None, db_path: str = None):
        super().__init__("SQL_Executor", llm_config)
        self.db_path = db_path
    
    def _get_system_message(self, **kwargs) -> str:
        return PROMPT
    
    def _get_agent_config(self) -> Dict[str, Any]:
        return {
            "human_input_mode": "NEVER",
            "max_consecutive_auto_reply": 1,
        }
    
    def create_agent(self, **kwargs) -> autogen.AssistantAgent:
        agent = super().create_agent(**kwargs)
        
        # 注册 SQL 执行函数
        @agent.register_for_llm(description="执行 SQL 语句")
        def execute_sql(sql: str) -> str:
            # TODO 数据一致性如何保证?
            if not self.db_path:
                raise ValueError(f"数据库{self.db_path}不存在")
            
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(sql)
                if sql.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    columns = [description[0] for description in cursor.description]
                    output = f"查询成功! 共 {len(results)} 条记录:\n"
                    output += " | ".join(columns) + "\n"
                    output += "-" * 50 + "\n"
                    for row in results:
                        output += " | ".join(str(val) for val in row) + "\n"
                    
                    conn.close()
                    return output
                else:
                    conn.commit()
                    conn.close()
                    return f"执行成功! 影响了 {cursor.rowcount} 行。"
                    
            except Exception as e:
                return f"ERROR: {str(e)}"
        
        return agent
