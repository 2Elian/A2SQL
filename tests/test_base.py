import unittest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class BaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema_file = "data/CSpider/db_schema.json"
        cls.test_db_id = "college_2"
    
    def setUp(self):
        pass
    
    def tearDown(self):
        pass
