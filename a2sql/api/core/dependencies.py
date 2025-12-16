from typing import Optional
from a2sql.utils import Config
from a2sql.executors import SQL2QaExecutor
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
) -> SQL2QaExecutor:
    global _executor_cache
    
    if force_new or dataset not in _executor_cache:
        config = get_config()
        schema_file = DATASET_SCHEMAS.get(dataset, config.get("default_schema_file"))
        llm_config = config.get_llm_config()
        db_config = config.get("db_config")
        # cache
        _executor_cache[dataset] = SQL2QaExecutor(
            schema_file=schema_file,
            llm_config=llm_config,
            db_config=db_config
        )
    
    return _executor_cache[dataset]


def init_dependencies():
    config = get_config()
    if not config.validate():
        raise RuntimeError("Configuration verification failed. Please check your environment variables.")
    
    default_dataset = config.get("default_dataset", "CSpider")
    get_executor(default_dataset)


def clear_cache():
    global _executor_cache
    _executor_cache.clear()
