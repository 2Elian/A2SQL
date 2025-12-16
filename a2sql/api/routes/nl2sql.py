from typing import List
from fastapi import APIRouter, HTTPException, Query
from a2sql.api.model import DatabaseInfo, SQL2QARequest, SQL2GenerateRequest, SQL2QAResponse, SQL2GenerateResponse
from a2sql.api.services.nl2sql_service import NL2SQLService
from a2sql.api.core.dependencies import get_config
from a2sql.core.execution_state import get_execution_state
from a2sql.utils import setup_logger

logger = setup_logger("api.routes.nl2sql")
router = APIRouter(prefix="/nl2sql", tags=["NL2SQL"])
"""
Interface Illustrate:
Interface1: sql2generate
    if not sql_exe:
        nl_analyst -> sql_generator -> end
    else:
        nl_analyst -> sql_generator -> sql_executor -> refiner -> end
Interface2: sql2qa
    if not sql_exe:
        raise
    nl_analyst -> sql_generator -> sql_executor -> refiner -> chat_generate -> end
"""

@router.get("/databases", response_model=List[str], summary="获取数据库列表")
async def list_databases(
    dataset: str = Query(default="CSpider", description="数据集名称 (CSpider/DuSQL/NL2SQL)")
) -> List[str]:
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
    try:
        db_info = NL2SQLService.get_database_info(db_id, dataset)
        return DatabaseInfo(**db_info)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取数据库信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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
    state = get_execution_state(task_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
    
    return state.to_dict()

@router.post("/sql2qa", response_model=SQL2QAResponse, summary="以聊天的方式与数据库进行交互")
async def execute_nl2sql(request: SQL2QARequest) -> SQL2QAResponse:
    try:
        result = NL2SQLService.execute_sql2qa(
            db_id=request.db_id,
            nl_query=request.nl_query,
            db_config=request.db_config.to_dict(),
            dataset=request.dataset,
            max_round=request.max_round
        )
        
        return SQL2QAResponse(
            status=result.status.value,
            data={"result": result.data} if result.is_success() else None,
            error=result.error,
            metadata=result.metadata
        )
    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Execution failed: {error_detail}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_detail)


@router.post("/sql2generate", response_model=SQL2GenerateResponse, summary="自然语言转换SQL语句接口")
async def generate_sql(request: SQL2GenerateRequest) -> SQL2GenerateResponse:
    try:
        result = NL2SQLService.execute_sql2generate(
            db_id=request.db_id,
            nl_query=request.nl_query,
            sql_exe=request.sql_exe,
            db_config=request.db_config.to_dict() if request.db_config else None,
            dataset=request.dataset,
            max_round=request.max_round
        )
        return SQL2GenerateResponse(
            status=result["status"],
            sql=result.get("sql"),
            error=result.get("error"),
            metadata=result.get("metadata")
        )
        
    except Exception as e:
        import traceback
        error_detail = f"{type(e).__name__}: {str(e)}"
        logger.error(f"SQL generation failed: {error_detail}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        return SQL2GenerateResponse(
            status="failed",
            sql=None,
            error=error_detail,
            metadata={
                "db_id": request.db_id,
                "nl_query": request.nl_query,
                "error_type": type(e).__name__
            }
        )