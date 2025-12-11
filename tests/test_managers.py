from tests.test_base import BaseTestCase
from a2sql.managers import SchemaManager


class TestSchemaManager(BaseTestCase):
    """测试 SchemaManager"""
    
    def test_initialization(self):
        """测试初始化"""
        manager = SchemaManager(self.schema_file)
        manager.initialize()
        
        self.assertTrue(manager.is_initialized())
        self.assertTrue(manager.validate())
    
    def test_get_schema_by_id(self):
        """测试根据 ID 获取 Schema"""
        manager = SchemaManager(self.schema_file)
        manager.initialize()
        
        schema = manager.get_schema_by_id(self.test_db_id)
        
        self.assertIsNotNone(schema)
        self.assertEqual(schema['db_id'], self.test_db_id)
        self.assertIn('table_names', schema)
    
    def test_get_all_db_ids(self):
        """测试获取所有数据库 ID"""
        manager = SchemaManager(self.schema_file)
        manager.initialize()
        
        db_ids = manager.get_all_db_ids()
        
        self.assertIsInstance(db_ids, list)
        self.assertGreater(len(db_ids), 0)
        self.assertIn(self.test_db_id, db_ids)
    
    def test_format_schema_for_prompt(self):
        """测试格式化 Schema"""
        manager = SchemaManager(self.schema_file)
        manager.initialize()
        
        prompt = manager.format_schema_for_prompt(self.test_db_id)
        
        self.assertIsInstance(prompt, str)
        self.assertIn("数据库名称", prompt)
        self.assertIn("表名", prompt)


if __name__ == "__main__":
    unittest.main()
