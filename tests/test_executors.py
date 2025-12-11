"""
测试 Executor
"""

from tests.test_base import BaseTestCase
from a2sql.executors import NL2SQLExecutor
from a2sql.core.base_executor import ExecutionStatus


class TestNL2SQLExecutor(BaseTestCase):
    """测试 NL2SQLExecutor"""
    
    def test_initialization(self):
        """测试初始化"""
        executor = NL2SQLExecutor(self.schema_file)
        
        self.assertIsNotNone(executor.schema_manager)
        self.assertIsNotNone(executor.agent_manager)
        self.assertIsNotNone(executor.task_manager)
    
    def test_get_available_databases(self):
        """测试获取可用数据库"""
        executor = NL2SQLExecutor(self.schema_file)
        
        databases = executor.get_available_databases()
        
        self.assertIsInstance(databases, list)
        self.assertGreater(len(databases), 0)
    
    def test_get_schema_info(self):
        """测试获取 Schema 信息"""
        executor = NL2SQLExecutor(self.schema_file)
        
        schema = executor.get_schema_info(self.test_db_id)
        
        self.assertIsNotNone(schema)
        self.assertEqual(schema['db_id'], self.test_db_id)


if __name__ == "__main__":
    unittest.main()
