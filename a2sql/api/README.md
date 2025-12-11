a2sql/api/
├── main.py                 # FastAPI 应用入口
├── core/                   # 核心模块
│   ├── constants.py       # 常量配置
│   ├── dependencies.py    # 依赖注入管理
│   └── __init__.py
├── middleware/            # 中间件
│   ├── exception_handler.py  # 全局异常处理
│   └── __init__.py
├── model/                 # 数据模型
│   ├── common.py         # 通用模型
│   ├── database.py       # 数据库模型
│   ├── health.py         # 健康检查模型
│   ├── nl2sql.py         # NL2SQL 模型
│   └── __init__.py
├── routes/                # 路由层
│   ├── nl2sql.py         # NL2SQL 路由
│   └── __init__.py
└── services/              # 业务逻辑层
    ├── nl2sql_service.py # NL2SQL 服务
    └── __init__.py