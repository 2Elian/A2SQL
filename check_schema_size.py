"""
检查 schema 的实际大小
"""
from a2sql.managers import SchemaManager

# 测试数据库
db_id = "43ad6bdc1d7111e988a6f40f24344a08"
schema_file = "data/NL2SQL/db_schema.json"

manager = SchemaManager(schema_file)
manager.initialize()

schema_prompt = manager.format_schema_for_prompt(db_id)

print("=" * 60)
print("Schema 信息")
print("=" * 60)
print(f"数据库 ID: {db_id}")
print(f"Schema 长度: {len(schema_prompt)} 字符")
print(f"预估 token 数: ~{len(schema_prompt) // 2} tokens (中文)")
print()
print("=" * 60)
print("Schema 内容预览 (前 1000 字符):")
print("=" * 60)
print(schema_prompt[:1000])
print("...")
print()
print("=" * 60)
print("Schema 内容预览 (后 500 字符):")
print("=" * 60)
print("..." + schema_prompt[-500:])
