from typing import List
from fastapi import APIRouter, HTTPException, Query
from a2sql.api.model import DatabaseInfo, NL2SQLRequest, NL2SQLResponse, SQLGenerateRequest, SQLGenerateResponse
from a2sql.api.services.nl2sql_service import NL2SQLService
from a2sql.api.core.dependencies import get_config
from a2sql.core.execution_state import get_execution_state
from a2sql.utils import setup_logger

logger = setup_logger("api.routes.nl2sql")
router = APIRouter(prefix="/nl2sql", tags=["NL2SQL"])

@router.get("/databases", response_model=List[str], summary="获取数据库列表")
async def list_databases(
    dataset: str = Query(default="CSpider", description="数据集名称 (CSpider/DuSQL/NL2SQL)")
) -> List[str]:
    """
    获取指定数据集的数据库列表
    
    Args:
        dataset: 数据集名称
        
    Returns:
        数据库 ID 列表
    """
    try:
        return NL2SQLService.get_databases(dataset)
    except Exception as e:
        logger.error(f"获取数据库列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/databases/{db_id}", response_model=DatabaseInfo, summary="获取数据库信息")
async def get_database_info(
    db_id: str,
    dataset: str = Query(default="CSpider", description="数据集名称 (CSpider/DuSQL/NL2SQL)")
) -> DatabaseInfo:
    """
    获取指定数据库的详细信息
    
    Args:
        db_id: 数据库 ID
        dataset: 数据集名称
        
    Returns:
        数据库详细信息
    """
    try:
        db_info = NL2SQLService.get_database_info(db_id, dataset)
        return DatabaseInfo(**db_info)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取数据库信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute", response_model=NL2SQLResponse, summary="执行 NL2SQL 转换")
async def execute_nl2sql(request: NL2SQLRequest) -> NL2SQLResponse:
    """
    执行 NL2SQL 转换任务
    
    Args:
        request: NL2SQL 请求模型
        
    Returns:
        NL2SQL 响应结果
    """
    try:
        logger.info(f"开始执行 NL2SQL: db_id={request.db_id}, query={request.nl_query[:50]}...")
        
        result = NL2SQLService.execute_nl2sql(
            db_id=request.db_id,
            nl_query=request.nl_query,
            dataset=request.dataset,
            max_round=request.max_round
        )
        
        logger.info(f"NL2SQL 执行完成: status={result.status.value}")
        
        return NL2SQLResponse(
            status=result.status.value,
            data={"result": result.data} if result.is_success() else None,
            error=result.error,
            metadata=result.metadata
        )
    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        logger.error(f"NL2SQL 执行失败: {error_detail}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/config", response_model=dict, summary="获取系统配置")
async def get_config_info() -> dict:
    config = get_config()
    return {
        "model_name": config.get("model_name"),
        "default_schema_file": config.get("default_schema_file"),
        "default_dataset": config.get("default_dataset", "CSpider"),
        "max_consecutive_auto_reply": config.get("max_consecutive_auto_reply"),
        "max_round": config.get("max_round"),
        "debug": config.get("debug"),
        "verbose": config.get("verbose"),
    }


@router.get("/state/{task_id}", response_model=dict, summary="获取任务执行状态")
async def get_task_state(task_id: str) -> dict:
    """
    获取指定任务的详细执行状态
    
    包含每个步骤的输入输出、执行时间、Agent对话历史等
    
    Args:
        task_id: 任务 ID
        
    Returns:
        任务执行状态的完整信息
    """
    state = get_execution_state(task_id)
    
    if not state:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    
    return state.to_dict()


@router.post("/generate", response_model=SQLGenerateResponse, summary="生成 SQL 语句(不执行)")
async def generate_sql(request: SQLGenerateRequest) -> SQLGenerateResponse:
    """
    只生成 SQL 语句,不执行 SQL
    
    复用完整的 NL2SQL 流程 (包括 NL_Analyst, SQL_Generator, SQL_Executor, Refiner),
    从最终结果中提取生成的 SQL 语句。
    
    Args:
        request: SQL 生成请求
        
    Returns:
        SQL 生成结果,包含生成的 SQL 语句
    """
    try:
        logger.info(f"开始生成 SQL: db_id={request.db_id}, query={request.nl_query[:50]}...")
        
        result = NL2SQLService.generate_sql_only(
            db_id=request.db_id,
            nl_query=request.nl_query,
            dataset=request.dataset
        )
        
        logger.info(f"SQL 生成完成: {result.get('sql', '')[:50] if result.get('sql') else 'None'}...")
        
        return SQLGenerateResponse(
            status=result["status"],
            sql=result.get("sql"),
            error=result.get("error"),
            metadata=result.get("metadata")
        )
        
    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        logger.error(f"SQL 生成失败: {error_detail}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return SQLGenerateResponse(
            status="failed",
            sql=None,
            error=error_detail,
            metadata={
                "db_id": request.db_id,
                "nl_query": request.nl_query,
                "error_type": type(e).__name__
            }
        )