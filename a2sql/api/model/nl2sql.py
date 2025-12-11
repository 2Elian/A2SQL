from typing import Optional
from pydantic import BaseModel, Field


class NL2SQLRequest(BaseModel):
    db_id: str = Field(..., description="数据库 ID")
    nl_query: str = Field(..., description="自然语言查询")
    max_round: int = Field(default=20, ge=1, le=50, description="最大对话轮数")
    dataset: str = Field(default="CSpider", description="数据集名称 (CSpider/DuSQL/NL2SQL)")
    
    class Config:
        json_json_schema_extra = {
            "example": {
                "db_id": "college_2",
                "nl_query": "查询所有在 Computer Science 部门工作的教师姓名和工资",
                "max_round": 20,
                "dataset": "CSpider"
            }
        }


class NL2SQLResponse(BaseModel):
    status: str = Field(..., description="执行状态")
    data: Optional[dict] = Field(None, description="响应数据")
    error: Optional[str] = Field(None, description="错误信息")
    metadata: Optional[dict] = Field(None, description="元数据")
    
    class Config:
        json_json_schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "result": {
                        "sql": "SELECT name, salary FROM instructor WHERE dept_name = 'Computer Science'"
                    }
                },
                "error": None,
                "metadata": {}
            }
        }


class SQLGenerateRequest(BaseModel):
    """只生成 SQL,不执行"""
    db_id: str = Field(..., description="数据库 ID")
    nl_query: str = Field(..., description="自然语言查询")
    dataset: str = Field(default="CSpider", description="数据集名称 (CSpider/DuSQL/NL2SQL)")
    
    class Config:
        json_json_schema_extra = {
            "example": {
                "db_id": "college_2",
                "nl_query": "查询所有在 Computer Science 部门工作的教师姓名和工资",
                "dataset": "CSpider"
            }
        }


class SQLGenerateResponse(BaseModel):
    """SQL 生成响应"""
    status: str = Field(..., description="执行状态: success/failed")
    sql: Optional[str] = Field(None, description="生成的 SQL 语句")
    error: Optional[str] = Field(None, description="错误信息")
    metadata: Optional[dict] = Field(None, description="元数据")
    
    class Config:
        json_json_schema_extra = {
            "example": {
                "status": "success",
                "sql": "SELECT name, salary FROM instructor WHERE dept_name = 'Computer Science'",
                "error": None,
                "metadata": {
                    "db_id": "college_2",
                    "nl_query": "查询所有在 Computer Science 部门工作的教师姓名和工资"
                }
            }
        }
