from typing import List, Dict, Any
import autogen

from a2sql.api.core.constants import DATASET_SCHEMAS
from a2sql.api.core.dependencies import get_executor, get_config
from a2sql.core.base_executor import ExecutionResult, ExecutionStatus
from a2sql.managers import SchemaManager, AgentManager
from a2sql.utils import setup_logger
from a2sql.utils.common_utils import extract_sql_from_result

logger = setup_logger("api.service")

class NL2SQLService:
    @staticmethod
    def execute_sql2qa(db_id: str, nl_query: str, db_config: dict, dataset: str = "CSpider", max_round: int = 20) -> ExecutionResult:
        try:
            logger.info(f"SQL2QA task: dataset={dataset}, db_id={db_id}, db_config={db_config.get('db_type')}, query:{nl_query}")
            executor = get_executor(dataset)
            executor.config['db_config'] = db_config
            
            result = executor.execute(db_id=db_id,nl_query=nl_query,max_round=max_round)
            
            logger.info(f"SQL2QA task completed: status={result.status.value}")
            return result
            
        except Exception as e:
            logger.error(f"SQL2QA task failed: {str(e)}")
            raise
    
    @staticmethod
    def execute_sql2generate(db_id: str, nl_query: str, sql_exe: bool = False, db_config: dict = None, dataset: str = "CSpider", max_round: int = 20) -> Dict[str, Any]:
        try:
            logger.info(f"SQL2Generate task: dataset={dataset}, db_id={db_id}, sql_exe={sql_exe}, query:{nl_query}")
            # TODO global_cache how to do?
            from a2sql.executors import SQL2GenerateExecutor
            from a2sql.api.core.dependencies import get_config
            config = get_config()
            schema_file = DATASET_SCHEMAS.get(dataset, config.get("default_schema_file"))
            if not schema_file:
                raise ValueError(f"Schema file not found for dataset: {dataset}")
            executor = SQL2GenerateExecutor(schema_file=schema_file,llm_config=config.get_llm_config(),db_config=db_config,sql_exe=sql_exe)
            
            result = executor.execute(db_id=db_id,nl_query=nl_query,max_round=max_round)
            sql = None
            if result.is_success() and result.data:
                sql = extract_sql_from_result(result.data)
            logger.info(f"SQL2Generate completed: status={result.status.value}")
            
            return {
                "status": result.status.value,
                "sql": sql,
                "error": result.error,
                "metadata": result.metadata
            }
            
        except Exception as e:
            logger.error(f"SQL2Generate failed: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise

    @staticmethod
    def get_databases(dataset: str = "CSpider") -> List[str]:
        try:
            executor = get_executor(dataset)
            databases = executor.get_available_databases()
            logger.info(f"Returns the {len(databases)} databases of the {dataset} dataset.")
            return databases
        except Exception as e:
            logger.error(f"Failed to retrieve database list: {str(e)}")
            raise
    
    @staticmethod
    def get_database_info(db_id: str, dataset: str = "CSpider") -> Dict[str, Any]:
        try:
            executor = get_executor(dataset)
            schema = executor.get_schema_info(db_id)
            if not schema:
                raise ValueError(f"The database {db_id} does not exist.")
            return {
                "db_id": db_id,
                "table_count": len(schema['table_names_original']),
                "tables": schema['table_names_original'],
                "columns": schema.get('column_names_original', []),
                "primary_keys": schema.get('primary_keys', []),
                "foreign_keys": schema.get('foreign_keys', [])
            }
        except Exception as e:
            logger.error(f"Failed to retrieve database information: {str(e)}")
            raise