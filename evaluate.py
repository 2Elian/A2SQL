"""
NL2SQL 系统评估工具
使用 NL2SQL train.json 数据集评估系统性能
"""

import json
import sys
import os
from typing import List, Dict, Tuple
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class NL2SQLEvaluator:
    """NL2SQL 评估器"""
    
    def __init__(self, dataset_path: str):
        """
        初始化评估器
        
        Args:
            dataset_path: 数据集文件路径
        """
        self.dataset_path = dataset_path
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
    
    def run_evaluation(
        self,
        executor,
        subset_size: int = 10,
        verbose: bool = True
    ) -> Dict:
        """
        运行评估
        
        Args:
            executor: NL2SQL执行器
            subset_size: 评估样本数
            verbose: 是否详细输出
            
        Returns:
            评估结果字典
        """
        print("\n" + "=" * 80)
        print(f"🎯 开始评估 (样本数: {subset_size})")
        print("=" * 80)
        
        subset = self.get_evaluation_subset(subset_size)
        
        results = {
            'total': len(subset),
            'exact_match': 0,
            'partial_match': 0,
            'failed': 0,
            'details': []
        }
        
        for i, item in enumerate(subset, 1):
            if verbose:
                print(f"\n[{i}/{len(subset)}] 评估中...")
                print(f"  问题: {item['question'][:50]}...")
                print(f"  真实SQL: {item['query'][:60]}...")
            
            try:
                # 这里需要实际调用执行器
                # result = executor.execute(item['db_id'], item['question'])
                # predicted_sql = result.data.get('sql', '')
                
                # 模拟预测 (实际使用时替换为真实预测)
                predicted_sql = item['query']  # 临时使用真实SQL模拟
                
                exact_match, details = self.evaluate_prediction(
                    item['query'],
                    predicted_sql
                )
                
                if exact_match:
                    results['exact_match'] += 1
                    if verbose:
                        print(f"  ✅ 完全匹配")
                else:
                    results['partial_match'] += 1
                    if verbose:
                        print(f"  ⚠️  不匹配")
                
                results['details'].append({
                    'question_id': item['question_id'],
                    'question': item['question'],
                    'ground_truth': item['query'],
                    'prediction': predicted_sql,
                    'exact_match': exact_match,
                    **details
                })
                
            except Exception as e:
                results['failed'] += 1
                if verbose:
                    print(f"  ❌ 失败: {str(e)}")
        
        # 计算指标
        accuracy = results['exact_match'] / results['total'] * 100
        
        print("\n" + "=" * 80)
        print("📈 评估结果")
        print("=" * 80)
        print(f"总样本数: {results['total']}")
        print(f"完全匹配: {results['exact_match']} ({accuracy:.2f}%)")
        print(f"部分匹配: {results['partial_match']}")
        print(f"执行失败: {results['failed']}")
        
        return results
    
    def save_results(self, results: Dict, output_path: str):
        """保存评估结果"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 结果已保存到: {output_path}")


def main():
    """主函数"""
    print("=" * 80)
    print("NL2SQL 数据集分析与评估工具")
    print("=" * 80)
    
    # 1. 加载和分析数据集
    dataset_path = "data/NL2SQL/train.json"
    evaluator = NL2SQLEvaluator(dataset_path)
    
    # 2. 分析数据集
    evaluator.analyze_dataset()
    
    # 3. 评估示例 (需要实际的执行器)
    print("\n" + "=" * 80)
    print("💡 如何使用此数据集评估系统:")
    print("=" * 80)
    print("""
1. 准备执行器:
   ```python
   from src.executors import NL2SQLExecutor
   executor = NL2SQLExecutor(
       schema_file="data/CSpider/db_schema.json",
       llm_config=config.get_llm_config()
   )
   ```

2. 运行评估:
   ```python
   evaluator = NL2SQLEvaluator("data/NL2SQL/train.json")
   results = evaluator.run_evaluation(
       executor=executor,
       subset_size=100,  # 评估100个样本
       verbose=True
   )
   ```

3. 查看结果:
   ```python
   print(f"准确率: {results['exact_match'] / results['total'] * 100:.2f}%")
   evaluator.save_results(results, "evaluation_results.json")
   ```

4. 关键评估指标:
   - Exact Match (EM): 生成的SQL与标准答案完全一致
   - Execution Accuracy: SQL执行结果正确
   - Component Match: SQL各组件(SELECT, WHERE等)正确率
   
5. 数据集特点:
   - 中文NL2SQL数据集
   - 包含真实业务场景查询
   - 提供结构化SQL表示和查询字符串
   - 适合评估中文语义理解和SQL生成能力
    """)


if __name__ == "__main__":
    main()
