from enum import Enum


class DatasetType(str, Enum):
    """数据集类型枚举"""
    CSPIDER = "CSpider"
    DUSQL = "DuSQL"
    NL2SQL = "NL2SQL"


# 数据集 Schema 文件映射
DATASET_SCHEMAS = {
    DatasetType.CSPIDER: "data/CSpider/db_schema.json",
    DatasetType.DUSQL: "data/DuSQL/db_schema.json",
    DatasetType.NL2SQL: "data/NL2SQL/db_schema.json"
}


# API 版本
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"


# CORS 配置
DEFAULT_CORS_ORIGINS = ["*"]


# 分页配置
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
