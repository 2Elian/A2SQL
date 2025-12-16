from typing import Optional
from a2sql.utils import Config
from a2sql.executors import SQL2QaExecutor, SQL2GenerateExecutor
from a2sql.api.core.constants import DATASET_SCHEMAS

_config: Optional[Config] = None
_qa_executor_cache = {}
_generate_executor_cache = {}


def get_config() -> Config:
    global _config
    if _config is None:
        _config = Config()
    return _config


def get_qa_executor(
    dataset: str = "CSpider",
    db_config: dict = None,
    force_new: bool = False
) -> SQL2QaExecutor:
    """
    获取 SQL2QA Executor (对话问答)
    
    Args:
        dataset: 数据集名称
        db_config: 数据库配置(必须)
        force_new: 是否强制创建新实例
    """
    global _qa_executor_cache
    
    # 生成缓存key(基于dataset和db_config)
    cache_key = f"{dataset}_{hash(str(db_config))}"
    
    if force_new or cache_key not in _qa_executor_cache:
        config = get_config()
        schema_file = DATASET_SCHEMAS.get(dataset, config.get("default_schema_file"))
        llm_config = config.get_llm_config()
        
        # 使用传入的db_config或配置文件中的
        if not db_config:
            db_path = config.get("database_path")
            db_config = config.get("db_config")
            if not db_config and db_path:
                db_config = {
                    "db_type": "sqlite",
                    "db_path": db_path
                }
        
        _qa_executor_cache[cache_key] = SQL2QaExecutor(
            schema_file=schema_file,
            llm_config=llm_config,
            db_config=db_config
        )
    
    return _qa_executor_cache[cache_key]


def get_generate_executor(
    dataset: str = "CSpider",
    db_config: dict = None,
    force_new: bool = False
) -> SQL2GenerateExecutor:
    """
    获取 SQL2Generate Executor (SQL生成)
    
    Args:
        dataset: 数据集名称
        db_config: 数据库配置(可选,仅sql_exe=True时需要)
        force_new: 是否强制创建新实例
    """
    global _generate_executor_cache
    
    # 生成缓存key
    cache_key = f"{dataset}_{hash(str(db_config))}"
    
    if force_new or cache_key not in _generate_executor_cache:
        config = get_config()
        schema_file = DATASET_SCHEMAS.get(dataset, config.get("default_schema_file"))
        llm_config = config.get_llm_config()
        
        _generate_executor_cache[cache_key] = SQL2GenerateExecutor(
            schema_file=schema_file,
            llm_config=llm_config,
            db_config=db_config
        )
    
    return _generate_executor_cache[cache_key]


# 为了向后兼容,保留旧的函数名
def get_executor(
    dataset: str = "CSpider",
    force_new: bool = False
) -> SQL2QaExecutor:
    """已废弃: 请使用 get_qa_executor"""
    return get_qa_executor(dataset=dataset, force_new=force_new)


def init_dependencies():
    config = get_config()
    if not config.validate():
        raise RuntimeError("Configuration verification failed. Please check your environment variables.")
    
    default_dataset = config.get("default_dataset", "CSpider")
    get_qa_executor(default_dataset)


def clear_cache():
    global _qa_executor_cache, _generate_executor_cache
    _qa_executor_cache.clear()
    _generate_executor_cache.clear()
