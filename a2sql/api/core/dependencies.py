from typing import Optional
from a2sql.utils import Config
from a2sql.executors import NL2SQLExecutor
from a2sql.api.core.constants import DATASET_SCHEMAS

_config: Optional[Config] = None
_executor_cache = {}


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config


def get_executor(
    dataset: str = "CSpider",
    force_new: bool = False
) -> NL2SQLExecutor:
    global _executor_cache
    
    if force_new or dataset not in _executor_cache:
        config = get_config()
        schema_file = DATASET_SCHEMAS.get(dataset, config.get("default_schema_file"))
        llm_config = config.get_llm_config()
        db_path = config.get("database_path")
        
        _executor_cache[dataset] = NL2SQLExecutor(
            schema_file=schema_file,
            llm_config=llm_config,
            db_path=db_path
        )
    
    return _executor_cache[dataset]


def init_dependencies():
    config = get_config()
    if not config.validate():
        raise RuntimeError("配置验证失败，请检查环境变量")
    
    default_dataset = config.get("default_dataset", "CSpider")
    get_executor(default_dataset)


def clear_cache():
    global _executor_cache
    _executor_cache.clear()
