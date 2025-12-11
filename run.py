import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from a2sql.executors import NL2SQLExecutor
from a2sql.utils import Config, setup_logger


def main():
    parser = argparse.ArgumentParser(description="NL2SQL AutoGen cli")
    parser.add_argument(
        "--db-id",
        type=str,
        required=True,
        help="数据库 ID"
    )
    
    parser.add_argument(
        "--query",
        type=str,
        required=True,
        help="自然语言查询"
    )
    
    parser.add_argument(
        "--schema-file",
        type=str,
        default="data/CSpider/db_schema.json",
        help="Schema 文件路径"
    )
    
    parser.add_argument(
        "--db-path",
        type=str,
        default=None,
        help="数据库文件路径(可选)"
    )
    
    parser.add_argument(
        "--max-round",
        type=int,
        default=20,
        help="最大对话轮次"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出"
    )
    
    args = parser.parse_args()
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = setup_logger("nl2sql", log_level)
    config = Config()
    
    if not config.validate():
        logger.error("配置验证失败,请检查环境变量")
        sys.exit(1)
    logger.info("初始化 NL2SQL 执行器...")
    
    executor = NL2SQLExecutor(
        schema_file=args.schema_file,
        llm_config=config.get_llm_config(),
        db_path=args.db_path
    )
    logger.info(f"执行 NL2SQL 任务: {args.query}")
    
    result = executor.execute(
        db_id=args.db_id,
        nl_query=args.query,
        max_round=args.max_round
    )
    if result.is_success():
        logger.info(f"任务执行成功: {result.data}")
    else:
        logger.error(f"任务执行失败: {result.error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
