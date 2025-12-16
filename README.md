<div align="center"> 

# A2SQL- 多智能体协作下的NL2SQL系统

</div>



## 项目概述

**Agent-to-SQL(a2sql)** 是一个基于AutoGen框架开发的NL2SQL-Agent 系统, 旨在为企业提供稳定、精准、可无缝集成到业务流程中的智能数据查询能力。A2SQL的核心架构围绕 **理解-生成-执行-反思** 四个关键步骤构建，确保在复杂查询场景下依旧保持高精度与强鲁棒性。欢迎大家star~⭐⭐。

## TODO

1. SQL生成准确率达95%以上

2. 纯SQL生成响应时间<1s

3. 对于多表结构上下文溢出的处理

4. 对数据库意图识别的处理
5. 埋点收集badcase与训练代码(dpo-badcase处理 / 蒸馏-模型迁移处理)集成至接口
6. MYSQL数据库一键导入a2sql接口，并考虑数据一致性与安全问题
7. 如何快速接入已有的项目？

```mermaid
graph TB
    subgraph "客户端层 Client Layer"
        A1[Web Frontend]
        A2[API Client]
        A3[Evaluation Tools]
    end
    
    subgraph "API网关层 API Gateway"
        B1[FastAPI Server<br/>localhost:8002]
        B2[CORS Middleware]
        B3[Exception Handler]
    end
    
    subgraph "路由层 Routes Layer"
        C1["/api/v1/nl2sql/query"<br/>完整查询]
        C2["/api/v1/nl2sql/generate"<br/>仅生成SQL]
        C3["/api/v1/nl2sql/state/{task_id}"<br/>状态查询]
    end
    
    subgraph "服务层 Service Layer"
        D1[NL2SQLService]
        D2[依赖注入<br/>get_executor]
        D3[全局缓存<br/>_executor_cache]
    end
    
    subgraph "执行层 Executor Layer"
        E1[NL2SQLExecutor]
        E2[ExecutionState<br/>状态管理]
        E3[ErrorDataLogger<br/>错误记录]
    end
    
    subgraph "管理层 Manager Layer"
        F1[SchemaManager<br/>Schema管理]
        F2[AgentManager<br/>Agent创建]
        F3[TaskManager<br/>任务协调]
    end
    
    subgraph "Agent协作层 Multi-Agent Layer"
        G1[User_Proxy<br/>任务发起]
        G2[NL_Analyst<br/>需求分析]
        G3[SQL_Generator<br/>SQL生成]
        G4[SQL_Executor<br/>SQL执行]
        G5[Refiner<br/>结果优化]
    end
    
    subgraph "LLM服务层 LLM Service"
        H1[OneAPI Gateway<br/>http://43.200.7.56:8087]
        H2[Qwen-30B Model<br/>qwen30b]
    end
    
    subgraph "数据层 Data Layer"
        I1[(NL2SQL Database<br/>SQLite)]
        I2[db_schema.json<br/>Schema定义]
        I3[dev.json<br/>测试数据]
    end
    
    subgraph "日志与监控层 Logging & Monitoring"
        J1[logs/nl2sql.log<br/>系统日志]
        J2[logs/error_data.log<br/>Badcase记录]
        J3[ExecutionState Store<br/>实时状态]
    end
    
    subgraph "工具层 Tools Layer"
        K1[evaluate.py<br/>性能评估]
        K2[view_badcases.py<br/>错误分析]
        K3[test_state_tracking.py<br/>状态测试]
    end
    
    %% 连接关系
    A1 --> B1
    A2 --> B1
    A3 --> B1
    
    B1 --> B2
    B2 --> B3
    B3 --> C1
    B3 --> C2
    B3 --> C3
    
    C1 --> D1
    C2 --> D1
    C3 --> J3
    
    D1 --> D2
    D2 --> D3
    D3 --> E1
    
    E1 --> E2
    E1 --> E3
    E1 --> F1
    E1 --> F2
    E1 --> F3
    
    F1 --> I2
    F2 --> G1
    F2 --> G2
    F2 --> G3
    F2 --> G4
    F2 --> G5
    
    F3 --> G1
    F3 --> G2
    F3 --> G3
    F3 --> G4
    F3 --> G5
    
    G1 -.对话.-> G2
    G2 -.对话.-> G3
    G3 -.对话.-> G4
    G4 -.对话.-> G5
    G5 -.对话.-> G1
    
    G2 --> H1
    G3 --> H1
    G4 --> H1
    G5 --> H1
    
    H1 --> H2
    
    G4 --> I1
    
    E2 --> J3
    E3 --> J2
    F3 --> J1
    
    K1 --> C2
    K2 --> J2
    K3 --> C3
    
    style B1 fill:#4CAF50,color:#fff
    style E1 fill:#2196F3,color:#fff
    style F3 fill:#FF9800,color:#fff
    style H1 fill:#9C27B0,color:#fff
    style J2 fill:#F44336,color:#fff
    style E2 fill:#00BCD4,color:#fff
```
---

### 架构图

```
# sql2qa
┌─────────────┐
│ User_Proxy  │  ← 协调者
└──────┬──────┘
       │
   ┌───┴───┐
   │       │
┌──▼───┐ ┌─▼──────┐
│ NL   │ │  SQL   │
│Analyst│ │Generator│       
└──┬───┘ └─┬──────┘
   │       │
   └───┬───┘
       │
  ┌────▼─────┐
  │   SQL    │
  │ Executor │
  └────┬─────┘
       │
  ┌────▼─────┐
  │ Refiner  │  ← 错误修正
  └──────────┘
```

---


# 致谢

先谢谢我自己哈哈哈哈哈