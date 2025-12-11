from enum import Enum


class DatasetType(str, Enum):
    CSPIDER = "CSpider"
    DUSQL = "DuSQL"
    NL2SQL = "NL2SQL"

DATASET_SCHEMAS = {
    DatasetType.CSPIDER: "data/CSpider/db_schema.json",
    DatasetType.DUSQL: "data/DuSQL/db_schema.json",
    DatasetType.NL2SQL: "data/NL2SQL/db_schema.json"
}


# API 版本
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

DEFAULT_CORS_ORIGINS = ["*"]


# 分页配置
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
