import autogen
import sqlite3
from typing import Dict, Any, Optional

from a2sql.core.base_agent import BaseAgent

class SQLExecutorAgent(BaseAgent):
    def __init__(
        self, 
        llm_config: Dict[str, Any] = None, 
        db_path: str = None,
        db_config: Optional[Dict[str, Any]] = None,
        prompt_template: str = None
    ):
        super().__init__("SQL_Executor", llm_config)
        if db_config:
            self.db_config = db_config
        elif db_path:
            self.db_config = {"db_path": db_path, "db_type": "sqlite"}
        else:
            self.db_config = {}
        
        self.prompt_template = prompt_template
    
    def _get_system_message(self, **kwargs) -> str:
        if not self.prompt_template:
            raise ValueError("SQLExecutorAgent requires prompt_template")
        return self.prompt_template
    
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
            db_type = self.db_config.get("db_type", "sqlite")
            
            if db_type == "sqlite":
                return self._execute_sqlite(sql)
            else:
                return f"ERROR: 暂不支持 {db_type} 数据库"
        
        return agent
    
    def _execute_sqlite(self, sql: str) -> str:
        """执行SQLite查询"""
        db_path = self.db_config.get("db_path")
        if not db_path:
            return "ERROR: 未配置数据库路径"
        
        try:
            conn = sqlite3.connect(db_path)
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
                return output + "\nTERMINATE"
            else:
                conn.commit()
                row_count = cursor.rowcount
                conn.close()
                return f"执行成功! 影响了 {row_count} 行。\n\nTERMINATE"
                
        except Exception as e:
            return f"ERROR: {str(e)}"
