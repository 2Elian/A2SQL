import json
from typing import Dict, List, Optional
from a2sql.core.base_manager import BaseManager
from a2sql.utils import get_logger, log_method_execution_time

logger = get_logger(__name__)


class SchemaManager(BaseManager):
    def __init__(self, schema_file: str):
        super().__init__({"schema_file": schema_file})
        self.schemas: List[Dict] = []
        self.schema_cache: Dict[str, Dict] = {}
    
    def initialize(self) -> None:
        schema_file = self.get_config("schema_file")
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                self.schemas = json.load(f)
            for schema in self.schemas:
                self.schema_cache[schema['db_id']] = schema
            
            self._initialized = True
            
        except Exception as e:
            raise RuntimeError(f"Failed to load schema file: {e}")
    
    def validate(self) -> bool:
        return self._initialized and len(self.schemas) > 0
    
    def get_schema_by_id(self, db_id: str) -> Optional[Dict]:
        if not self.is_initialized():
            self.initialize()
        
        return self.schema_cache.get(db_id)
    
    def get_all_db_ids(self) -> List[str]:
        if not self.is_initialized():
            self.initialize()
        
        return list(self.schema_cache.keys())
    
    @log_method_execution_time
    def format_schema_for_prompt(self, db_id: str) -> str:
        logger.info(f"Formatting schema for db: {db_id}")
        
        schema = self.get_schema_by_id(db_id)
        if not schema:
            logger.error(f"Database not found: {db_id}")
            return f"Database {db_id} not found"
        
        logger.info(f"Schema info: {len(schema['table_names_original'])} tables")
        
        prompt = f"[重要上下文:数据库 Schema]\n"
        prompt += f"数据库名称: {schema['db_id']}\n\n"
        for table_idx, table_name in enumerate(schema['table_names_original']):
            prompt += f"表名: {table_name}\n"
            columns = []
            for col_idx, (tbl_idx, col_name) in enumerate(schema['column_names_original']):
                if tbl_idx == table_idx:
                    col_type = schema['column_types'][col_idx]
                    is_pk = col_idx in schema['primary_keys']
                    pk_mark = " (主键)" if is_pk else ""
                    columns.append(f"  - {col_name} ({col_type}){pk_mark}")
            
            prompt += "列:\n" + "\n".join(columns) + "\n"
            fks = []
            for fk in schema['foreign_keys']:
                if schema['column_names_original'][fk[0]][0] == table_idx:
                    col_from = schema['column_names_original'][fk[0]][1]
                    table_to_idx = schema['column_names_original'][fk[1]][0]
                    table_to = schema['table_names_original'][table_to_idx]
                    col_to = schema['column_names_original'][fk[1]][1]
                    fks.append(f"  - {col_from} 引用 {table_to}.{col_to}")
            
            if fks:
                prompt += "外键:\n" + "\n".join(fks) + "\n"
            
            prompt += "\n"
        
        prompt += "约束: 你的所有操作必须基于此 Schema。\n"
        
        return prompt
