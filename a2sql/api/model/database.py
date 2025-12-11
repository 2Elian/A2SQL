from typing import List
from pydantic import BaseModel, Field


class DatabaseInfo(BaseModel):
    """Database information model"""
    
    db_id: str = Field(..., description="数据库 ID")
    table_count: int = Field(..., description="表数量")
    tables: List[str] = Field(..., description="表名列表")
    
    class Config:
        json_json_schema_extra = {
            "example": {
                "db_id": "college_2",
                "table_count": 5,
                "tables": ["instructor", "course", "department", "student", "enrollment"]
            }
        }
