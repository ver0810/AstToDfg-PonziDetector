#!/usr/bin/env python3
"""
Batch detector for processing multiple JSON files asynchronously.
"""

import json
import os
import asyncio
import glob
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
from tqdm.asyncio import tqdm_asyncio

from .llm_detector import PonziDetectionPipeline, LLMConfig
from ..utils.functional_helpers import Result


class BatchDetector:
    """Batch processor for detecting Ponzi schemes in multiple files"""
    
    def __init__(self, config: LLMConfig = None, concurrency_limit: int = 40, cache_dir: str = "cache"):
        """
        Initialize batch detector.
        
        Args:
            config: LLM configuration
            concurrency_limit: Maximum concurrent requests
            cache_dir: Directory for caching results
        """
        self.config = config or LLMConfig()
        self.concurrency_limit = concurrency_limit
        self.cache_dir = cache_dir
        self.pipeline = PonziDetectionPipeline(config, cache_dir)
        
        # Create output directories
        os.makedirs("results", exist_ok=True)
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_json_files(self, output_dir: str = "output", pattern: str = "*.json") -> List[Tuple[str, str]]:
        """
        Get all JSON files from output directory.
        
        Args:
            output_dir: Directory containing JSON files
            pattern: File pattern to match
            
        Returns:
            List of (file_name, file_path) tuples
        """
        search_pattern = os.path.join(output_dir, pattern)
        files = sorted(glob.glob(search_pattern))
        
        if not files:
            print(f"❌ 未找到 {output_dir} 目录下的 {pattern} 文件")
            return []
        
        print(f"✅ 找到 {len(files)} 个文件")
        return [(Path(f).stem, f) for f in files]
    
    async def detect_batch(self, output_dir: str = "output", 
                          pattern: str = "*.json",
                          limit: int = None) -> Dict:
        """
        Batch detect Ponzi schemes from JSON files.
        
        Args:
            output_dir: Directory containing JSON files
            pattern: File pattern to match
            limit: Optional limit on number of files to process
            
        Returns:
            Dictionary with detection results and statistics
        """
        print("🚀 启动批量异步检测系统")
        print(f"📂 输入目录: {output_dir}")
        print(f"🔗 并发限制: {self.concurrency_limit}")
        
        # Get files to process
        json_files = self.get_json_files(output_dir, pattern)
        if not json_files:
            return {
                'error': '未找到文件',
                'total': 0,
                'successful': 0,
                'failed': 0
            }
        
        # Apply limit if specified
        if limit and limit > 0:
            json_files = json_files[:limit]
            print(f"⚠️  限制处理: {limit} 个文件")
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.concurrency_limit)
        
        async def process_file(file_info: Tuple[str, str]) -> Dict:
            """Process a single file"""
            file_name, file_path = file_info
            async with semaphore:
                try:
                    # Load JSON file
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Convert to string for analysis
                    contract_data = json.dumps(data, indent=2, ensure_ascii=False)
                    
                    # Detect
                    result = await self.pipeline.detect(contract_data, file_name)
                    
                    # Get label if exists
                    label = data.get('label', data.get('contract_label', -1))
                    
                    return {
                        'file_name': file_name,
                        'status': 'success',
                        'result': result,
                        'label': label
                    }
                    
                except Exception as e:
                    return {
                        'file_name': file_name,
                        'status': 'error',
                        'error': str(e)
                    }
        
        # Process all files concurrently
        print(f"\n📊 开始处理 {len(json_files)} 个文件...\n")
        
        tasks = [process_file(file_info) for file_info in json_files]
        results = await tqdm_asyncio.gather(*tasks, desc="🔍 检测进度")
        
        # Calculate statistics
        return self._calculate_statistics(results)
    
    def _calculate_statistics(self, results: List[Dict]) -> Dict:
        """Calculate statistics from detection results"""
        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'error']
        
        stats = {
            'total': len(results),
            'successful': len(successful),
            'failed': len(failed),
            'detection_results': [],
            'statistics': {},
            'evaluation_metrics': {}
        }
        
        # Collect detection results
        ponzi_count = 0
        legitimate_count = 0
        confidence_scores = []
        
        # Confusion matrix
        tp = tn = fp = fn = 0
        
        for result in successful:
            classification = result['result']['classification_result']
            is_ponzi = classification['is_ponzi']
            confidence = classification['confidence']
            actual_label = result.get('label', -1)
            
            if is_ponzi:
                ponzi_count += 1
            else:
                legitimate_count += 1
            
            confidence_scores.append(confidence)
            
            stats['detection_results'].append({
                'file': result['file_name'],
                'is_ponzi': is_ponzi,
                'confidence': confidence,
                'risk_level': classification['risk_level'],
                'actual_label': actual_label
            })
            
            # Calculate confusion matrix (if labels available)
            if actual_label >= 0:
                actual_is_ponzi = bool(actual_label)
                if actual_is_ponzi and is_ponzi:
                    tp += 1
                elif not actual_is_ponzi and not is_ponzi:
                    tn += 1
                elif not actual_is_ponzi and is_ponzi:
                    fp += 1
                elif actual_is_ponzi and not is_ponzi:
                    fn += 1
        
        # Statistics
        if confidence_scores:
            stats['statistics'] = {
                'ponzi_detected': ponzi_count,
                'legitimate_detected': legitimate_count,
                'avg_confidence': sum(confidence_scores) / len(confidence_scores),
                'max_confidence': max(confidence_scores),
                'min_confidence': min(confidence_scores)
            }
        
        # Evaluation metrics
        total_with_labels = tp + tn + fp + fn
        if total_with_labels > 0:
            correct = tp + tn
            accuracy = correct / total_with_labels
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            stats['evaluation_metrics'] = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1_score,
                'confusion_matrix': {
                    'tp': tp,
                    'tn': tn,
                    'fp': fp,
                    'fn': fn
                },
                'total': total_with_labels,
                'correct': correct
            }
        
        # Add failed files info
        if failed:
            stats['failed_files'] = [
                {'file': r['file_name'], 'error': r['error']} 
                for r in failed
            ]
        
        return stats
    
    def print_statistics(self, stats: Dict):
        """Print statistics in a formatted way"""
        print("\n" + "="*50)
        print("✅ 批量检测完成！")
        print("="*50)
        print(f"📊 处理统计:")
        print(f"  总文件数: {stats['total']}")
        print(f"  ✅ 成功: {stats['successful']}")
        print(f"  ❌ 失败: {stats['failed']}")
        
        if stats['statistics']:
            print(f"\n🔍 检测结果:")
            print(f"  🔴 庞氏骗局数: {stats['statistics']['ponzi_detected']}")
            print(f"  🟢 合法合约数: {stats['statistics']['legitimate_detected']}")
            print(f"  📈 平均置信度: {stats['statistics']['avg_confidence']:.2%}")
            print(f"  ⬆️  最高置信度: {stats['statistics']['max_confidence']:.2%}")
            print(f"  ⬇️  最低置信度: {stats['statistics']['min_confidence']:.2%}")
        
        # Evaluation metrics
        if 'evaluation_metrics' in stats and stats['evaluation_metrics']:
            metrics = stats['evaluation_metrics']
            print(f"\n📊 性能评估指标:")
            print(f"  ✅ 准确率 (Accuracy):  {metrics['accuracy']:.2%}")
            print(f"  🔍 精确率 (Precision): {metrics['precision']:.2%}")
            print(f"  📈 召回率 (Recall):    {metrics['recall']:.2%}")
            print(f"  ⭐ F1 分数:           {metrics['f1_score']:.4f}")
            print(f"  🧮 正确预测: {metrics['correct']}/{metrics['total']}")
            print(f"  📈 混淆矩阵:")
            cm = metrics['confusion_matrix']
            print(f"      TP: {cm['tp']:<3} | FP: {cm['fp']:<3}")
            print(f"      FN: {cm['fn']:<3} | TN: {cm['tn']:<3}")
        else:
            print(f"\n⚠️  暂无标签数据，无法计算性能指标")
        
        if stats['failed'] > 0 and 'failed_files' in stats:
            print(f"\n⚠️  失败文件 ({stats['failed']}):")
            for fail in stats['failed_files'][:5]:
                print(f"  - {fail['file']}: {fail['error']}")
            if stats['failed'] > 5:
                print(f"  ... 还有 {stats['failed'] - 5} 个失败文件")
    
    def save_results(self, stats: Dict, output_prefix: str = "batch_detection") -> str:
        """
        Save detection results to file.
        
        Args:
            stats: Statistics dictionary
            output_prefix: Prefix for output filename
            
        Returns:
            Path to saved file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"results/{output_prefix}_{timestamp}.json"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 详细结果已保存: {result_file}")
        
        # Save ponzi-only report
        ponzi_files = [r for r in stats.get('detection_results', []) if r['is_ponzi']]
        if ponzi_files:
            report_file = f"results/ponzi_detected_{timestamp}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(ponzi_files, f, indent=2, ensure_ascii=False)
            print(f"🔴 庞氏骗局报告: {report_file}")
        
        return result_file
