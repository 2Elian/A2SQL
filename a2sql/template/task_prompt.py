PROMPT: str = """[用户初始 NL 查询]
目标: 开发并执行一个 NL2SQL 任务。

自然语言查询: "{nl_query}"

请开始:
1. NL_Analyst: 分析上述自然语言查询的意图
2. SQL_Generator: 根据分析结果生成 SQL 语句
3. SQL_Executor: 执行 SQL 并返回结果
4. 如果出现错误,Refiner 协助修正
5. 完成后回复 TERMINATE"""