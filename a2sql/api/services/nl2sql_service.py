from typing import List, Dict, Any
from a2sql.api.core.dependencies import get_executor
from a2sql.core.base_executor import ExecutionResult
from a2sql.utils import setup_logger

logger = setup_logger("api.service")


class NL2SQLService:
    @staticmethod
    def get_databases(dataset: str = "CSpider") -> List[str]:
        try:
            executor = get_executor(dataset)
            databases = executor.get_available_databases()
            logger.info(f"返回 {dataset} 数据集的 {len(databases)} 个数据库")
            return databases
        except Exception as e:
            logger.error(f"获取数据库列表失败: {str(e)}")
            raise
    
    @staticmethod
    def get_database_info(db_id: str, dataset: str = "CSpider") -> Dict[str, Any]:
        try:
            executor = get_executor(dataset)
            schema = executor.get_schema_info(db_id)
            if not schema:
                raise ValueError(f"数据库 {db_id} 不存在")
            return {
                "db_id": db_id,
                "table_count": len(schema['table_names_original']),
                "tables": schema['table_names_original'],
                "columns": schema.get('column_names_original', []),
                "primary_keys": schema.get('primary_keys', []),
                "foreign_keys": schema.get('foreign_keys', [])
            }
        except Exception as e:
            logger.error(f"获取数据库信息失败: {str(e)}")
            raise
    
    @staticmethod
    def execute_nl2sql(
        db_id: str,
        nl_query: str,
        dataset: str = "CSpider",
        max_round: int = 20
    ) -> ExecutionResult:
        try:
            logger.info(f"收到 NL2SQL 请求: dataset={dataset}, db={db_id}, query={nl_query}")
            executor = get_executor(dataset)
            result = executor.execute(
                db_id=db_id,
                nl_query=nl_query,
                max_round=max_round
            )
            
            logger.info(f"NL2SQL 任务完成: status={result.status.value}")
            return result
            
        except Exception as e:
            logger.error(f"NL2SQL 执行失败: {str(e)}")
            raise
