import re


def extract_sql_from_result(result_data: str) -> str:
    if not result_data:
        return None
    sql = result_data.strip()
    if '```sql' in sql:
        sql = sql.split('```sql')[1].split('```')[0].strip()
    elif '```' in sql:
        sql = sql.split('```')[1].split('```')[0].strip()
    lines = sql.split('\n')
    for i, line in enumerate(lines):
        line_stripped = line.strip().upper()
        if line_stripped.startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH')):
            sql = '\n'.join(lines[i:]).strip()
            break
    
    return sql if sql else result_data