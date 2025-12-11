try:
    from contextlib import asynccontextmanager
except ImportError:
    from contextlib2 import asynccontextmanager # type: ignore

from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
import signal
import asyncio

# 重要！禁用代理, 避免 autogen 请求被代理拦截
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''
os.environ['NO_PROXY'] = '*'
os.environ['no_proxy'] = '*'

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from a2sql.utils import Config, setup_logger
from a2sql.api.core.dependencies import init_dependencies, get_config
from a2sql.api.routes import nl2sql_router
from a2sql.api.middleware.exception_handler import register_exception_handlers

logger = setup_logger("api", log_file="logs/api.log")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 正在启动 NL2SQL API 服务...")
    init_dependencies()
    logger.info("✅ NL2SQL API 服务启动成功") 
    yield
    logger.info("👋 NL2SQL API 服务正在关闭...")


def create_app() -> FastAPI:
    app = FastAPI(
        title="NL2SQL AutoGen API",
        description="todo",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    config = get_config()
    origins = config.get("cors_origins", "*").split(",") if config.get("cors_origins") else ["*"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册全局异常处理器
    register_exception_handlers(app)
    
    # 注册路由
    app.include_router(nl2sql_router, prefix="/api/v1")
    @app.get("/", tags=["Root"])
    async def root():
        """API 根路径"""
        return {
            "message": "NL2SQL AutoGen API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs"
        }
    @app.get("/health", tags=["Health"])
    async def health_check():
        """健康检查端点"""
        config = get_config()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "config_valid": config.validate()
        }
    
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    
    config = get_config()
    host = config.get("api_host", "0.0.0.0")
    port = int(config.get("api_port", 8001))
    def signal_handler(sig, frame):
        logger.info(f"收到信号 {sig}，正在关闭服务...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    logger.info(f"启动服务: {host}:{port}")
    try:
        uvicorn.run(
            "a2sql.api.main:app",
            host=host,
            port=port,
            reload=config.get("debug", False),
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("收到 Ctrl+C，服务正在关闭...")
    except Exception as e:
        logger.error(f"服务异常退出: {str(e)}")
    finally:
        logger.info("服务已关闭")
