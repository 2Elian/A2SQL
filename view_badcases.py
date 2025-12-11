"""
查看和分析 badcase 日志
"""
import json
from datetime import datetime
from collections import Counter
import sys


def view_badcases(log_file: str = "logs/error_data.log", limit: int = None):
    """
    查看 badcase 日志
    
    Args:
        log_file: 日志文件路径
        limit: 显示条数限制
    """
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ 日志文件不存在: {log_file}")
        return
    
    if not lines:
        print("✅ 暂无 badcase 记录")
        return
    
    badcases = [json.loads(line) for line in lines]
    
    if limit:
        badcases = badcases[-limit:]
    
    print("=" * 80)
    print(f"Badcase 统计 (共 {len(badcases)} 条)")
    print("=" * 80)
    
    # 统计错误类型
    error_types = Counter([bc['error']['type'] for bc in badcases])
    print("\n【错误类型分布】")
    for error_type, count in error_types.most_common():
        print(f"  {error_type}: {count} 次")
    
    # 统计失败步骤
    failed_steps = Counter([bc['error']['failed_step'] for bc in badcases])
    print("\n【失败步骤分布】")
    for step, count in failed_steps.most_common():
        print(f"  {step}: {count} 次")
    
    # 显示详细记录
    print("\n" + "=" * 80)
    print("详细记录")
    print("=" * 80)
    
    for i, bc in enumerate(badcases, 1):
        print(f"\n【Badcase #{i}】")
        print(f"时间: {bc['timestamp']}")
        print(f"任务ID: {bc['task_id']}")
        print(f"数据库ID: {bc['db_id']}")
        print(f"自然语言查询: {bc['nl_query']}")
        print(f"\n错误信息:")
        print(f"  类型: {bc['error']['type']}")
        print(f"  消息: {bc['error']['message']}")
        print(f"  失败步骤: {bc['error']['failed_step']} ({bc['error']['step_type']})")
        
        if bc['error'].get('traceback'):
            print(f"\n  错误堆栈 (前500字符):")
            traceback_preview = bc['error']['traceback'][:500]
            print(f"  {traceback_preview}")
            if len(bc['error']['traceback']) > 500:
                print(f"  ... (还有 {len(bc['error']['traceback']) - 500} 字符)")
        
        # 显示执行状态
        if bc.get('execution_state') and bc['execution_state'].get('steps'):
            print(f"\n  执行步骤:")
            for step in bc['execution_state']['steps']:
                status_icon = "✅" if step['status'] == 'success' else "❌"
                print(f"    {status_icon} {step['step_name']} ({step['status']})")
        
        print("-" * 80)


def analyze_badcases(log_file: str = "logs/error_data.log"):
    """
    分析 badcase 模式
    """
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"❌ 日志文件不存在: {log_file}")
        return
    
    badcases = [json.loads(line) for line in lines]
    
    print("=" * 80)
    print("Badcase 深度分析")
    print("=" * 80)
    
    # 按数据库分组
    db_errors = {}
    for bc in badcases:
        db_id = bc['db_id']
        if db_id not in db_errors:
            db_errors[db_id] = []
        db_errors[db_id].append(bc)
    
    print(f"\n【问题数据库 TOP 10】")
    sorted_dbs = sorted(db_errors.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for db_id, errors in sorted_dbs:
        print(f"  {db_id}: {len(errors)} 次失败")
    
    # 常见错误消息
    error_messages = Counter([bc['error']['message'][:100] for bc in badcases])
    print(f"\n【常见错误消息 TOP 5】")
    for msg, count in error_messages.most_common(5):
        print(f"  {count} 次: {msg}...")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='查看 NL2SQL badcase 日志')
    parser.add_argument('--file', default='logs/error_data.log', help='日志文件路径')
    parser.add_argument('--limit', type=int, help='显示最近N条记录')
    parser.add_argument('--analyze', action='store_true', help='执行深度分析')
    
    args = parser.parse_args()
    
    if args.analyze:
        analyze_badcases(args.file)
    else:
        view_badcases(args.file, args.limit)
