"""
NL2SQL 系统完整流程演示
展示从自然语言到 SQL 的完整执行过程
(纯演示版本,不需要实际依赖)
"""
"""
📋 流程步骤
1. 初始化阶段
plaintext
Config → SchemaManager → AgentManager → TaskManager → NL2SQLExecutor
Config: 加载环境变量(API Key, 模型名称等)
SchemaManager: 加载并解析数据库 Schema JSON
AgentManager: 准备创建 5 个 Agent
TaskManager: 准备管理任务执行
NL2SQLExecutor: 整合所有组件
2. Schema 处理
python
# SchemaManager.format_schema_for_prompt()
JSON Schema → 格式化文本 → Agent 提示词
3. Agent 创建
python
# 基于 BaseAgent 基类
for agent_type in [NLAnalyst, SQLGenerator, SQLExecutor, Refiner]:
    agent = agent_type.create_agent(schema=schema_prompt)
    # 每个 Agent 都有自己的系统消息和配置
4. 执行查询
用户输入: "查询所有在 Computer Science 部门工作的教师姓名和工资"Agent 对话流程:
User_Proxy 发起任务
plaintext
向所有 Agent 广播: "开始执行 NL2SQL 任务"
NL_Analyst 分析意图
plaintext
输入: "查询所有在 Computer Science 部门工作的教师姓名和工资"
输出: {
  操作类型: SELECT
  目标表: instructor
  目标列: name, salary
  WHERE条件: dept_name = 'Computer Science'
}
SQL_Generator 生成 SQL
plaintext
输入: NL_Analyst 的分析结果 + Schema
处理: 匹配表名和列名
输出: SELECT name, salary 
      FROM instructor 
      WHERE dept_name = 'Computer Science'
SQL_Executor 执行 SQL
plaintext
输入: SQL 语句
执行: 连接数据库并执行
输出: 成功 → 返回结果集
      失败 → 返回错误信息
Refiner (如果失败)
plaintext
输入: 错误信息
分析: 找出错误原因
输出: 修正建议 → SQL_Generator 重新生成
User_Proxy 终止
plaintext
收到成功结果 → 发送 "TERMINATE"
🔍 关键设计特点
1. 基类继承体系
plaintext
BaseAgent (抽象基类)
├── NLAnalystAgent
├── SQLGeneratorAgent
├── SQLExecutorAgent
└── RefinerAgent

BaseManager (抽象基类)
├── SchemaManager
├── AgentManager
└── TaskManager

BaseExecutor (抽象基类)
└── NL2SQLExecutor
2. 数据流向
plaintext
用户查询
  ↓
NL2SQLExecutor.execute()
  ↓
SchemaManager.format_schema_for_prompt()
  ↓
AgentManager.create_agents(schema)
  ↓
TaskManager.create_groupchat(agents)
  ↓
AutoGen GroupChat 多轮对话
  ↓
ExecutionResult(status, data, error)
3. 错误处理循环
plaintext
SQL_Generator → SQL → SQL_Executor
                ↓ (失败)
              ERROR
                ↓
            Refiner 分析
                ↓
          修正建议
                ↓
      SQL_Generator 重试
💡 核心优势
模块化: 每个组件职责单一,易于维护
可扩展: 通过继承基类轻松添加新 Agent
灵活性: 支持 CLI、API、代码三种使用方式
智能化: 自动错误修正,循环优化
企业级: 完整的配置、日志、测试体系

"""

def print_section(title: str):
    """打印章节标题"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")


def demo_complete_workflow():
    """演示完整工作流程"""
    
    print_section("🚀 NL2SQL 系统完整流程演示")
    
    # ============================================================================
    # 步骤 1: 初始化配置
    # ============================================================================
    print_section("步骤 1: 初始化配置")
    
    print("📝 加载环境变量和配置...")
    
    print(f"  ✓ Model: gpt-4")
    print(f"  ✓ Schema File: data/CSpider/db_schema.json")
    print(f"  ✓ Max Round: 20")
    
    # ============================================================================
    # 步骤 2: 创建执行器
    # ============================================================================
    print_section("步骤 2: 创建 NL2SQL 执行器")
    
    print("🔧 初始化执行器,包含:")
    print("  - SchemaManager: 管理数据库 Schema")
    print("  - AgentManager: 管理所有 Agent")
    print("  - TaskManager: 管理任务执行")
    
    print("\n✅ 执行器初始化完成!")
    print(f"  - Schema Manager: ✓")
    print(f"  - Agent Manager: ✓")
    print(f"  - Task Manager: ✓")
    
    # ============================================================================
    # 步骤 3: 查看可用数据库
    # ============================================================================
    print_section("步骤 3: 查看可用数据库")
    
    databases = ["college_2", "flight_company", "perpetrator", "icfp_1", "cre_Doc_Template_Mgt"]
    print(f"📊 系统中有 {len(databases)} 个数据库 (示例):")
    for i, db_id in enumerate(databases[:5], 1):
        print(f"  {i}. {db_id}")
    
    # ============================================================================
    # 步骤 4: 选择数据库并查看 Schema
    # ============================================================================
    print_section("步骤 4: 选择数据库并查看 Schema")
    
    db_id = "college_2"
    print(f"🎯 选择数据库: {db_id}")
    
    tables = ["classroom", "department", "course", "instructor", "section", "student"]
    print(f"\n📋 数据库信息:")
    print(f"  - 数据库 ID: {db_id}")
    print(f"  - 表数量: {len(tables)}")
    print(f"  - 表名称: {', '.join(tables[:5])}...")
    
    # ============================================================================
    # 步骤 5: Schema 格式化为提示词
    # ============================================================================
    print_section("步骤 5: Schema 格式化")
    
    print("🔄 将 Schema 转换为 Agent 可理解的格式...")
    
    schema_prompt = """[重要上下文:数据库 Schema]
数据库名称: college_2

表名: instructor
列:
  - ID (text) (主键)
  - name (text)
  - dept_name (text)
  - salary (number)
外键:
  - dept_name 引用 department.dept_name

表名: department
列:
  - dept_name (text) (主键)
  - building (text)
  - budget (number)
"""
    
    print(f"\n生成的 Schema 提示词 (示例):")
    print("-" * 80)
    print(schema_prompt[:400])
    print("...")
    print("-" * 80)
    
    # ============================================================================
    # 步骤 6: 创建所有 Agent
    # ============================================================================
    print_section("步骤 6: 创建 Agent 团队")
    
    print("👥 创建 5 个专业 Agent:")
    
    agent_info = [
        ("User_Proxy", "用户代理", "协调整个流程"),
        ("NL_Analyst", "NL 分析师", "分析自然语言意图"),
        ("SQL_Generator", "SQL 生成器", "生成 SQL 语句"),
        ("SQL_Executor", "SQL 执行器", "执行 SQL 并返回结果"),
        ("Refiner", "错误修正专家", "诊断和修正 SQL 错误")
    ]
    
    for name, role, desc in agent_info:
        print(f"\n  ✓ {name}")
        print(f"    角色: {role}")
        print(f"    职责: {desc}")
    
    print(f"\n✅ 共创建 5 个 Agent")
    
    # ============================================================================
    # 步骤 7: 准备自然语言查询
    # ============================================================================
    print_section("步骤 7: 准备自然语言查询")
    
    nl_query = "查询所有在 Computer Science 部门工作的教师姓名和工资"
    
    print(f"💬 用户输入:")
    print(f"  '{nl_query}'")
    
    print(f"\n🔍 这个查询需要:")
    print(f"  1. NL_Analyst 识别意图:")
    print(f"     - 操作类型: SELECT")
    print(f"     - 目标表: instructor")
    print(f"     - 目标列: name, salary")
    print(f"     - 过滤条件: dept_name = 'Computer Science'")
    
    print(f"\n  2. SQL_Generator 生成 SQL:")
    print(f"     - 基于 Schema 匹配表名和列名")
    print(f"     - 生成正确的 WHERE 条件")
    print(f"     - 输出纯 SQL 语句")
    
    print(f"\n  3. SQL_Executor 执行 SQL:")
    print(f"     - 执行生成的 SQL")
    print(f"     - 返回结果或错误信息")
    
    print(f"\n  4. Refiner (如果需要):")
    print(f"     - 如果 SQL 执行失败")
    print(f"     - 分析错误原因")
    print(f"     - 提供修正建议")
    print(f"     - SQL_Generator 重新生成")
    
    # ============================================================================
    # 步骤 8: 执行流程图
    # ============================================================================
    print_section("步骤 8: 执行流程可视化")
    
    print("""
    用户查询: "查询 CS 部门的教师姓名和工资"
         │
         ▼
    ┌─────────────────┐
    │  User_Proxy     │  接收查询,启动流程
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  NL_Analyst     │  分析意图
    │                 │  → 操作: SELECT
    │                 │  → 表: instructor
    │                 │  → 列: name, salary
    │                 │  → 条件: dept_name = 'CS'
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ SQL_Generator   │  生成 SQL
    │                 │  → SELECT name, salary
    │                 │     FROM instructor
    │                 │     WHERE dept_name = 'Computer Science'
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ SQL_Executor    │  执行 SQL
    │                 │  → 连接数据库
    │                 │  → 执行查询
    │                 │  → 返回结果
    └────────┬────────┘
             │
             ├─── 成功 ──→ 返回结果 ──→ TERMINATE
             │
             └─── 失败 ──┐
                        │
                        ▼
                ┌─────────────────┐
                │    Refiner      │  错误修正
                │                 │  → 分析错误
                │                 │  → 提供建议
                └────────┬────────┘
                         │
                         └──→ 返回 SQL_Generator
    """)
    
    # ============================================================================
    # 步骤 9: 执行任务 (模拟)
    # ============================================================================
    print_section("步骤 9: 执行 NL2SQL 任务")
    
    print("⚡ 开始执行任务...")
    print("\n注意: 由于需要 OpenAI API Key,这里只演示流程结构")
    print("实际执行时,Agents 会进行多轮对话直到完成任务\n")
    
    print("模拟执行过程:")
    print("\n  [User_Proxy → All Agents]")
    print("  '请开始执行 NL2SQL 任务'")
    
    print("\n  [NL_Analyst → SQL_Generator]")
    print("  '分析结果:")
    print("   - 操作类型: SELECT")
    print("   - 目标表: instructor")
    print("   - 目标列: name, salary")
    print("   - WHERE 条件: dept_name = \"Computer Science\"'")
    
    print("\n  [SQL_Generator → SQL_Executor]")
    print("  'SELECT name, salary FROM instructor")
    print("   WHERE dept_name = \"Computer Science\"'")
    
    print("\n  [SQL_Executor → User_Proxy]")
    print("  '模拟执行成功: SQL 语句格式正确(未连接实际数据库)'")
    
    print("\n  [User_Proxy → All]")
    print("  'TERMINATE - 任务完成'")
    
    # ============================================================================
    # 步骤 10: 结果总结
    # ============================================================================
    print_section("步骤 10: 系统特点总结")
    
    print("✨ 系统核心特点:\n")
    
    print("1️⃣  基类继承架构")
    print("   - BaseAgent: 所有 Agent 继承统一接口")
    print("   - BaseManager: 所有 Manager 继承统一管理模式")
    print("   - BaseExecutor: 执行器继承统一执行流程")
    
    print("\n2️⃣  分层模块化设计")
    print("   - Core: 定义抽象接口")
    print("   - Agents: 实现具体 Agent 逻辑")
    print("   - Managers: 管理资源和生命周期")
    print("   - Executors: 编排执行流程")
    print("   - Utils: 提供工具支持")
    
    print("\n3️⃣  智能错误修正")
    print("   - Refiner Agent 自动诊断错误")
    print("   - 提供具体修正建议")
    print("   - 循环重试直到成功")
    
    print("\n4️⃣  多种使用方式")
    print("   - CLI 命令行")
    print("   - FastAPI REST API")
    print("   - Python 代码集成")
    
    print("\n5️⃣  企业级特性")
    print("   - 完整的配置管理")
    print("   - 结构化日志系统")
    print("   - 单元测试覆盖")
    print("   - 类型提示和文档")
    
    # ============================================================================
    # 实际执行示例 (需要 API Key)
    # ============================================================================
    print_section("实际执行示例")
    
    print("如果配置了 OPENAI_API_KEY,可以实际执行:")
    print("\n```python")
    print("result = executor.execute(")
    print("    db_id='college_2',")
    print("    nl_query='查询所有在 Computer Science 部门工作的教师'")
    print(")")
    print("")
    print("if result.is_success():")
    print("    print('成功:', result.data)")
    print("else:")
    print("    print('失败:', result.error)")
    print("```")
    
    print("\n" + "="*80)
    print("  演示完成! 🎉")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        demo_complete_workflow()
    except Exception as e:
        print(f"\n❌ 演示过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
