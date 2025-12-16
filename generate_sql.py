"""
Generate SQL predictions for NL2SQL dataset
"""
import json
import requests
import time
import re
from datetime import datetime


def clean_sql(sql: str) -> str:
    """Clean predicted SQL to NL2SQL format"""
    if not sql:
        return "SELECT *"
    
    # Check if SQL starts with valid keywords
    sql_upper = sql.strip().upper()
    valid_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'WITH']
    
    is_valid = False
    for keyword in valid_keywords:
        if sql_upper.startswith(keyword):
            is_valid = True
            break
    
    if not is_valid:
        return "SELECT *"
    
    # Remove FROM Table_xxx or FROM "Table_xxx"
    sql = re.sub(r'\s+FROM\s+"?Table_[A-Fa-f0-9]+"?', '', sql, flags=re.IGNORECASE)
    sql = re.sub(r'\s+FROM\s+"?[A-Za-z_][A-Za-z0-9_]*"?', '', sql, flags=re.IGNORECASE)
    
    # Remove quotes from column names in SELECT
    sql = re.sub(r'SELECT\s+"([^"]+)"', r'SELECT \1', sql, flags=re.IGNORECASE)
    
    # Remove quotes from column names in WHERE
    sql = re.sub(r'"([^"]+)"\s*(==|=|>|<|>=|<=|!=)', r'\1 \2', sql)
    
    # Unify to ==
    sql = sql.replace(' = ', ' == ')
    
    # Remove semicolon and clean spaces
    sql = sql.rstrip(';').strip()
    sql = ' '.join(sql.split())
    
    # Final check: if cleaned SQL is empty or too short, return SELECT *
    if not sql:
        return "SELECT *"
    
    return sql


def generate_predictions(
    dataset_path: str,
    api_url: str = "http://localhost:8002/api/v1/nl2sql/generate",
    output_file: str = "predictions.sql",
    dataset_name: str = "NL2SQL",
    limit: int = None
):
    """Generate SQL predictions for dataset"""
    
    print("="*80)
    print("SQL Generation Tool")
    print("="*80)
    print(f"Dataset: {dataset_path}")
    print(f"API: {api_url}")
    print(f"Output: {output_file}")
    print("="*80)
    
    # Load dataset
    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if limit:
        data = data[:limit]
    
    print(f"\nLoaded {len(data)} samples")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Generate predictions
    results = []
    start_time = time.time()
    
    for i, item in enumerate(data, 1):
        print(f"[{i}/{len(data)}] Processing qid: {item['question_id']}")
        
        try:
            # Call API
            response = requests.post(
                api_url,
                json={
                    "db_id": item['db_id'],
                    "nl_query": item['question'],
                    "dataset": dataset_name
                },
                timeout=300
            )
            
            result = response.json()
            
            if result['status'] == 'success' and result.get('sql'):
                sql = clean_sql(result['sql'])
                results.append({
                    'qid': item['question_id'],
                    'sql': sql,
                    'db_id': item['db_id']
                })
                if sql == "SELECT *":
                    print(f"  Warning: Invalid SQL, marked as SELECT *")
                else:
                    print(f"  Success: {sql[:60]}...")
            else:
                error = result.get('error', 'Unknown error')
                print(f"  Failed: {error}")
                results.append({
                    'qid': item['question_id'],
                    'sql': 'SELECT *',
                    'db_id': item['db_id']
                })
        
        except Exception as e:
            print(f"  Error: {str(e)}")
            results.append({
                'qid': item['question_id'],
                'sql': 'SELECT *',
                'db_id': item['db_id']
            })
    
    # Save to SQL file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("qid\tSQL query\tdb_id\n")
        for r in results:
            f.write(f"{r['qid']}\t{r['sql']}\t{r['db_id']}\n")
    
    total_time = time.time() - start_time
    success_count = sum(1 for r in results if r['sql'])
    
    print("\n" + "="*80)
    print("Summary")
    print("="*80)
    print(f"Total: {len(results)}")
    print(f"Success: {success_count}")
    print(f"Failed: {len(results) - success_count}")
    print(f"Time: {total_time:.2f}s")
    print(f"Avg: {total_time/len(results):.2f}s/sample")
    print(f"\nOutput saved to: {output_file}")
    print("="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate SQL predictions')
    parser.add_argument('--data', default='data/DuSQL/dev.json', help='Dataset path')
    parser.add_argument('--api', default='http://localhost:8002/api/v1/nl2sql/nl2sql', help='API URL')
    parser.add_argument('--output', default='predictions.sql', help='Output SQL file')
    parser.add_argument('--dataset', default='DuSQL', help='Dataset name')
    parser.add_argument('--limit', type=int, help='Limit number of samples')
    
    args = parser.parse_args()
    
    generate_predictions(
        dataset_path=args.data,
        api_url=args.api,
        output_file=args.output,
        dataset_name=args.dataset,
        limit=args.limit
    )
