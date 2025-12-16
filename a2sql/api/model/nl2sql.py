from typing import Optional
from pydantic import BaseModel, Field, field_validator


class DatabaseConfig(BaseModel):
    db_type: str = Field(default="sqlite", description="数据库类型: sqlite/mysql/postgresql")
    host: Optional[str] = Field(None, description="数据库主机地址")
    port: Optional[int] = Field(None, description="数据库端口")
    user: Optional[str] = Field(None, description="数据库用户名")
    password: Optional[str] = Field(None, description="数据库密码")
    database: Optional[str] = Field(None, description="数据库名称")
    db_path: Optional[str] = Field(None, description="SQLite数据库文件路径")
    
    @field_validator('db_path')
    def validate_sqlite_config(cls, v, values):
        db_type = values.get('db_type', 'sqlite')
        if db_type == 'sqlite' and not v:
            raise ValueError("SQLite requires db_path")
        return v
    
    @field_validator('host')
    def validate_remote_db_config(cls, v, values):
        db_type = values.get('db_type', 'sqlite')
        if db_type in ['mysql', 'postgresql']:
            if not v:
                raise ValueError(f"{db_type} requires host")
            if not values.get('port'):
                raise ValueError(f"{db_type} requires port")
            if not values.get('user'):
                raise ValueError(f"{db_type} requires user")
            if not values.get('database'):
                raise ValueError(f"{db_type} requires database name")
        return v
    
    def to_dict(self):
        return self.model_dump(exclude_none=True)


class NL2SQLCommonRequest(BaseModel):
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


class SQL2QARequest(BaseModel):
    db_id: str = Field(..., description="数据库 ID")
    nl_query: str = Field(..., description="自然语言查询")
    db_config: DatabaseConfig = Field(..., description="数据库连接配置")
    max_round: int = Field(default=20, ge=1, le=50, description="最大对话轮数")
    dataset: str = Field(default="CSpider", description="数据集名称")
    
    class Config:
        json_schema_extra = {
            "example": {
                "db_id": "college_2",
                "nl_query": "查询2023年总收入",
                "db_config": {
                    "db_type": "mysql",
                    "host": "localhost",
                    "port": 3306,
                    "user": "root",
                    "password": "password",
                    "database": "test_db"
                },
                "max_round": 20,
                "dataset": "CSpider"
            }
        }


class SQL2GenerateRequest(BaseModel):
    db_id: str = Field(..., description="数据库 ID")
    nl_query: str = Field(..., description="自然语言查询")
    sql_exe: bool = Field(default=False, description="是否执行SQL验证")
    db_config: Optional[DatabaseConfig] = Field(None, description="数据库连接配置")
    max_round: int = Field(default=20, ge=1, le=50, description="最大对话轮数")
    dataset: str = Field(default="CSpider", description="数据集名称")
    
    @field_validator('db_config')
    def validate_db_config_when_sql_exe(cls, v, values):
        sql_exe = values.get('sql_exe', False)
        if sql_exe and not v:
            raise ValueError("db_config is required when sql_exe=True")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "db_id": "college_2",
                "nl_query": "查询2023年总收入",
                "sql_exe": True,
                "db_config": {
                    "db_type": "sqlite",
                    "db_path": "/path/to/database.db"
                },
                "max_round": 20,
                "dataset": "CSpider"
            }
        }


class SQL2QAResponse(BaseModel):
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


class SQL2GenerateResponse(BaseModel):
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
