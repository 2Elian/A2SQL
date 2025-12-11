"""
NL2SQL 系统评估工具
使用 dev.json 数据集调用 API 评估系统性能
"""

import json
import sys
import os
import requests
import time
from typing import List, Dict, Tuple
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class NL2SQLEvaluator:
    """NL2SQL 评估器"""
    
    def __init__(self, dataset_path: str, api_url: str = "http://localhost:8002/api/v1/nl2sql/generate"):
        """
        初始化评估器
        
        Args:
            dataset_path: 数据集文件路径
            api_url: API 接口地址
        """
        self.dataset_path = dataset_path
        self.api_url = api_url
        self.data = []
        self.load_dataset()
    
    def load_dataset(self):
        """加载数据集"""
        print(f"📂 加载数据集: {self.dataset_path}")
        
        with open(self.dataset_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        print(f"✅ 成功加载 {len(self.data)} 条数据\n")
    
    def analyze_dataset(self):
        """分析数据集结构"""
        print("=" * 80)
        print("📊 数据集分析")
        print("=" * 80)
        
        # 基本统计
        print(f"\n1️⃣  基本信息:")
        print(f"   总样本数: {len(self.data)}")
        print(f"   样本字段: {list(self.data[0].keys())}")
        
        # 数据库统计
        db_counts = defaultdict(int)
        for item in self.data:
            db_counts[item['db_id']] += 1
        
        print(f"\n2️⃣  数据库分布:")
        print(f"   唯一数据库数: {len(db_counts)}")
        print(f"   前5个数据库:")
        for i, (db_id, count) in enumerate(sorted(db_counts.items(), key=lambda x: -x[1])[:5], 1):
            print(f"     {i}. {db_id}: {count} 条查询")
        
        # SQL 类型统计
        agg_types = defaultdict(int)
        cond_conn_types = defaultdict(int)
        
        for item in self.data:
            sql = item['sql']
            # 聚合类型
            for agg in sql.get('agg', []):
                agg_types[agg] += 1
            # 条件连接类型
            cond_conn_types[sql.get('cond_conn_op', 0)] += 1
        
        print(f"\n3️⃣  SQL 特征统计:")
        print(f"   聚合函数分布:")
        agg_names = {0: 'NONE', 1: 'MAX', 2: 'MIN', 3: 'COUNT', 4: 'COUNT', 5: 'SUM', 6: 'AVG'}
        for agg, count in sorted(agg_types.items()):
            print(f"     {agg_names.get(agg, f'AGG_{agg}')}: {count}")
        
        print(f"\n   条件连接符分布:")
        conn_names = {0: 'NONE', 1: 'AND', 2: 'OR'}
        for conn, count in sorted(cond_conn_types.items()):
            print(f"     {conn_names.get(conn, f'CONN_{conn}')}: {count}")
        
        # 问题长度统计
        question_lengths = [len(item['question']) for item in self.data]
        avg_length = sum(question_lengths) / len(question_lengths)
        
        print(f"\n4️⃣  问题特征:")
        print(f"   平均问题长度: {avg_length:.1f} 字符")
        print(f"   最短问题: {min(question_lengths)} 字符")
        print(f"   最长问题: {max(question_lengths)} 字符")
        
        # 样本示例
        print(f"\n5️⃣  数据样本示例:")
        for i in range(min(3, len(self.data))):
            item = self.data[i]
            print(f"\n   示例 {i+1}:")
            print(f"     数据库ID: {item['db_id']}")
            print(f"     问题: {item['question']}")
            print(f"     SQL: {item['query']}")
            print(f"     问题ID: {item['question_id']}")
    
    def get_evaluation_subset(self, n: int = 100) -> List[Dict]:
        """
        获取评估子集
        
        Args:
            n: 子集大小
            
        Returns:
            评估样本列表
        """
        import random
        
        # 确保可重现
        random.seed(42)
        
        # 按数据库分层采样
        db_samples = defaultdict(list)
        for item in self.data:
            db_samples[item['db_id']].append(item)
        
        # 从每个数据库采样
        subset = []
        samples_per_db = max(1, n // len(db_samples))
        
        for db_id, samples in db_samples.items():
            subset.extend(random.sample(samples, min(samples_per_db, len(samples))))
        
        # 如果不够,再随机补充
        if len(subset) < n:
            remaining = [item for item in self.data if item not in subset]
            subset.extend(random.sample(remaining, min(n - len(subset), len(remaining))))
        
        return subset[:n]
    
    def evaluate_prediction(
        self, 
        ground_truth: str, 
        prediction: str
    ) -> Tuple[bool, Dict]:
        """
        评估单个预测结果
        
        Args:
            ground_truth: 真实SQL
            prediction: 预测SQL
            
        Returns:
            (是否完全匹配, 评估详情)
        """
        # 标准化SQL (去除空格、大小写等)
        def normalize_sql(sql: str) -> str:
            sql = sql.strip().upper()
            sql = ' '.join(sql.split())
            return sql
        
        gt_norm = normalize_sql(ground_truth)
        pred_norm = normalize_sql(prediction)
        
        # 完全匹配
        exact_match = (gt_norm == pred_norm)
        
        # 部分匹配评估
        details = {
            'exact_match': exact_match,
            'gt_length': len(ground_truth),
            'pred_length': len(prediction),
            'has_select': 'SELECT' in pred_norm,
            'has_where': 'WHERE' in pred_norm,
            'has_and': 'AND' in pred_norm,
            'has_or': 'OR' in pred_norm,
        }
        
        return exact_match, details
    
    def call_api(self, db_id: str, question: str, dataset: str = "NL2SQL") -> Dict:
        """
        调用 API 生成 SQL
        
        Args:
            db_id: 数据库 ID
            question: 自然语言查询
            dataset: 数据集名称
            
        Returns:
            API 响应结果
        """
        payload = {
            "db_id": db_id,
            "nl_query": question,
            "dataset": dataset
        }
        
        try:
            response = requests.post(self.api_url, json=payload, timeout=300)
            return response.json()
        except Exception as e:
            return {
                "status": "failed",
                "sql": None,
                "error": str(e)
            }
    
    def run_evaluation(
        self,
        subset_size: int = None,
        dataset: str = "NL2SQL",
        verbose: bool = True,
        save_errors: bool = True
    ) -> Dict:
        """
        运行评估
        
        Args:
            subset_size: 评估样本数 (None 表示全部)
            dataset: 数据集名称
            verbose: 是否详细输出
            save_errors: 是否保存错误案例
            
        Returns:
            评估结果字典
        """
        print("\n" + "=" * 80)
        print(f"🎯 开始评估")
        print("=" * 80)
        print(f"API 地址: {self.api_url}")
        print(f"数据集: {dataset}")
        print(f"样本数: {subset_size if subset_size else '全部'}")
        print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # 确定评估子集
        if subset_size:
            subset = self.get_evaluation_subset(subset_size)
        else:
            subset = self.data
        
        results = {
            'total': len(subset),
            'exact_match': 0,
            'failed': 0,
            'success': 0,
            'total_time': 0,
            'details': [],
            'errors': []
        }
        
        start_time = time.time()
        
        for i, item in enumerate(subset, 1):
            print(f"\n[{i}/{len(subset)}] 评估中...")
            
            if verbose:
                print(f"  问题ID: {item['question_id']}")
                print(f"  数据库: {item['db_id']}")
                print(f"  问题: {item['question']}")
                print(f"  标准SQL: {item['query'][:80]}...")
            
            item_start = time.time()
            
            try:
                # 调用 API
                response = self.call_api(item['db_id'], item['question'], dataset)
                item_time = time.time() - item_start
                
                if response['status'] == 'success' and response.get('sql'):
                    predicted_sql = response['sql']
                    results['success'] += 1
                    
                    # 评估预测结果
                    exact_match, eval_details = self.evaluate_prediction(
                        item['query'],
                        predicted_sql
                    )
                    
                    if exact_match:
                        results['exact_match'] += 1
                        if verbose:
                            print(f"  ✅ 完全匹配 ({item_time:.2f}s)")
                    else:
                        if verbose:
                            print(f"  ⚠️  不匹配 ({item_time:.2f}s)")
                            print(f"     预测SQL: {predicted_sql[:80]}...")
                    
                    results['details'].append({
                        'question_id': item['question_id'],
                        'db_id': item['db_id'],
                        'question': item['question'],
                        'ground_truth': item['query'],
                        'prediction': predicted_sql,
                        'exact_match': exact_match,
                        'time': item_time,
                        **eval_details
                    })
                else:
                    # API 调用失败
                    results['failed'] += 1
                    error_msg = response.get('error', 'Unknown error')
                    
                    if verbose:
                        print(f"  ❌ API 失败: {error_msg}")
                    
                    error_case = {
                        'question_id': item['question_id'],
                        'db_id': item['db_id'],
                        'question': item['question'],
                        'ground_truth': item['query'],
                        'error': error_msg,
                        'time': item_time
                    }
                    results['errors'].append(error_case)
                    results['details'].append({
                        **error_case,
                        'exact_match': False,
                        'prediction': None
                    })
                
                results['total_time'] += item_time
                
            except Exception as e:
                results['failed'] += 1
                item_time = time.time() - item_start
                results['total_time'] += item_time
                
                if verbose:
                    print(f"  ❌ 异常: {str(e)}")
                
                error_case = {
                    'question_id': item['question_id'],
                    'db_id': item['db_id'],
                    'question': item['question'],
                    'ground_truth': item['query'],
                    'error': f"{type(e).__name__}: {str(e)}",
                    'time': item_time
                }
                results['errors'].append(error_case)
                results['details'].append({
                    **error_case,
                    'exact_match': False,
                    'prediction': None
                })
        
        # 计算指标
        total_time = time.time() - start_time
        accuracy = results['exact_match'] / results['total'] * 100 if results['total'] > 0 else 0
        avg_time = results['total_time'] / results['total'] if results['total'] > 0 else 0
        
        print("\n" + "=" * 80)
        print("📈 评估结果")
        print("=" * 80)
        print(f"总样本数: {results['total']}")
        print(f"成功生成: {results['success']} ({results['success']/results['total']*100:.2f}%)")
        print(f"完全匹配: {results['exact_match']} (准确率: {accuracy:.2f}%)")
        print(f"失败数量: {results['failed']}")
        print(f"总耗时: {total_time:.2f}s")
        print(f"平均耗时: {avg_time:.2f}s/样本")
        print("=" * 80)
        
        # 保存错误案例
        if save_errors and results['errors']:
            error_file = f"evaluation_errors_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(results['errors'], f, ensure_ascii=False, indent=2)
            print(f"\n❌ {len(results['errors'])} 个错误案例已保存到: {error_file}")
        
        return results
    
    def save_results(self, results: Dict, output_path: str):
        """保存评估结果"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 结果已保存到: {output_path}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NL2SQL 评估工具')
    parser.add_argument('--data', default='data/NL2SQL/dev.json', help='数据集路径')
    parser.add_argument('--api', default='http://localhost:8002/api/v1/nl2sql/generate', help='API 地址')
    parser.add_argument('--dataset', default='NL2SQL', help='数据集名称')
    parser.add_argument('--limit', type=int, help='评估样本数限制')
    parser.add_argument('--output', default='evaluation_results.json', help='结果保存路径')
    parser.add_argument('--analyze-only', action='store_true', help='仅分析数据集,不评估')
    parser.add_argument('--quiet', action='store_true', help='简化输出')
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("NL2SQL 评估工具")
    print("=" * 80)
    
    # 加载评估器
    evaluator = NL2SQLEvaluator(args.data, args.api)
    
    # 分析数据集
    if args.analyze_only:
        evaluator.analyze_dataset()
        return
    
    # 运行评估
    results = evaluator.run_evaluation(
        subset_size=args.limit,
        dataset=args.dataset,
        verbose=not args.quiet,
        save_errors=True
    )
    
    # 保存结果
    evaluator.save_results(results, args.output)
    
    print("\n✅ 评估完成!")


if __name__ == "__main__":
    main()
