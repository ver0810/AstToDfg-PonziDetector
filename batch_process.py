#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量处理JSON文件中的Solidity合约,生成DFG而不生成可视化
"""

import json
import os
import sys
from pathlib import Path
import time
from datetime import datetime
from typing import Dict, List, Tuple

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.analyzer import SolidityAnalyzer
from src.dfg_config import DFGConfig, OutputMode


class BatchProcessor:
    """批量处理Solidity合约的DFG生成器"""
    
    def __init__(self, input_file: str, output_dir: str, mode: OutputMode = OutputMode.STANDARD):
        """
        初始化批量处理器
        
        Args:
            input_file: 输入JSON文件路径
            output_dir: 输出目录路径
            mode: DFG输出模式 (COMPACT/STANDARD/VERBOSE)
        """
        self.input_file = input_file
        self.output_dir = Path(output_dir)
        self.mode = mode
        
        # 生成时间戳（格式：20251021_143229）
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 统计信息
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'total_nodes_before': 0,
            'total_nodes_after': 0,
            'total_time': 0.0
        }
        
        # 错误记录
        self.errors: List[Tuple[int, str]] = []
        
    def load_contracts(self) -> List[Dict]:
        """
        从JSONL文件加载合约
        
        Returns:
            合约列表
        """
        contracts = []
        print(f"📖 正在加载合约数据: {self.input_file}")
        
        with open(self.input_file, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    contracts.append({
                        'line_no': line_no,
                        'code': data.get('code', ''),
                        'label': data.get('label', 0)
                    })
                except json.JSONDecodeError as e:
                    print(f"⚠️  警告: 第{line_no}行JSON解析失败: {e}")
                    self.stats['skipped'] += 1
                    
        print(f"✅ 成功加载 {len(contracts)} 个合约")
        return contracts
    
    def process_contract(self, contract_data: Dict, index: int) -> bool:
        """
        处理单个合约
        
        Args:
            contract_data: 合约数据 {'line_no', 'code', 'label'}
            index: 合约索引
            
        Returns:
            是否成功
        """
        line_no = contract_data['line_no']
        code = contract_data['code']
        label = contract_data['label']
        
        # 跳过空代码
        if not code or not code.strip():
            self.stats['skipped'] += 1
            return False
        
        try:
            # 创建临时文件
            temp_file = self.output_dir / f"temp_contract_{index}.sol"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # 创建配置
            mode_config_map = {
                OutputMode.COMPACT: DFGConfig.compact(),
                OutputMode.STANDARD: DFGConfig.standard(),
                OutputMode.VERBOSE: DFGConfig.verbose()
            }
            config = mode_config_map[self.mode]
            
            # 分析合约（传入配置）
            analyzer = SolidityAnalyzer(
                solidity_version="0.4.x",
                output_dir=str(self.output_dir),
                dfg_config=config
            )
            
            # 构建AST
            ast_root = analyzer.ast_builder.build_ast(code)
            if not ast_root:
                self.errors.append((line_no, "Failed to build AST"))
                temp_file.unlink()
                return False
            
            # 提取合约名称
            contract_name = analyzer._extract_contract_name(ast_root) or f"Contract_{index}"
            
            # 处理0.4.x特性
            if analyzer.legacy_handler:
                analyzer._process_legacy_features(ast_root)
            
            # 构建DFG
            dfg = analyzer.dfg_builder.build_dfg(ast_root, contract_name)
            if not dfg:
                self.errors.append((line_no, "Failed to build DFG"))
                temp_file.unlink()
                return False
            
            # 删除临时文件
            temp_file.unlink()
            
            # 生成文件名：contract_{索引}_{时间戳}
            # 索引从0开始（index-1），因为index从1开始
            output_file = self.output_dir / f"contract_{index-1}_{self.timestamp}.json"
            
            # 使用JSONSerializer保存
            dfg_json = analyzer.json_serializer.serialize_dfg(dfg)
            
            # 添加元数据
            dfg_json['metadata'] = {
                'index': index - 1,  # 从0开始的索引
                'source_line': line_no,
                'label': label,
                'mode': self.mode.value,
                'contract_name': contract_name,
                'timestamp': self.timestamp
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(dfg_json, f, indent=2, ensure_ascii=False)
            
            # 更新统计
            ast_node_count = analyzer._count_ast_nodes(ast_root)
            self.stats['total_nodes_before'] += ast_node_count
            self.stats['total_nodes_after'] += len(dfg.nodes)
            
            return True
            
        except Exception as e:
            error_msg = f"第{line_no}行处理失败: {str(e)}"
            self.errors.append((line_no, str(e)))
            return False
    
    def process_all(self, progress_interval: int = 100):
        """
        处理所有合约
        
        Args:
            progress_interval: 每处理多少个合约显示一次进度
        """
        contracts = self.load_contracts()
        self.stats['total'] = len(contracts)
        
        print(f"\n🚀 开始批量处理 (模式: {self.mode.value})")
        print(f"📁 输出目录: {self.output_dir}")
        print(f"=" * 60)
        
        start_time = time.time()
        
        for idx, contract in enumerate(contracts, 1):
            # 显示进度
            if idx % progress_interval == 0 or idx == 1:
                elapsed = time.time() - start_time
                rate = idx / elapsed if elapsed > 0 else 0
                eta = (len(contracts) - idx) / rate if rate > 0 else 0
                
                print(f"📊 进度: {idx}/{len(contracts)} ({idx*100//len(contracts)}%) | "
                      f"成功: {self.stats['success']} | "
                      f"失败: {self.stats['failed']} | "
                      f"速率: {rate:.1f} contracts/s | "
                      f"预计剩余: {eta/60:.1f}分钟")
            
            # 处理合约
            success = self.process_contract(contract, idx)
            
            if success:
                self.stats['success'] += 1
            else:
                self.stats['failed'] += 1
        
        self.stats['total_time'] = time.time() - start_time
        
        # 显示最终统计
        self.print_summary()
        
        # 保存错误日志
        if self.errors:
            self.save_error_log()
    
    def print_summary(self):
        """打印处理摘要"""
        print(f"\n{'='*60}")
        print("📈 批量处理完成!")
        print(f"{'='*60}")
        print(f"总合约数:     {self.stats['total']}")
        print(f"成功处理:     {self.stats['success']} ({self.stats['success']*100//self.stats['total']}%)")
        print(f"处理失败:     {self.stats['failed']}")
        print(f"跳过:         {self.stats['skipped']}")
        print(f"总耗时:       {self.stats['total_time']:.1f} 秒")
        print(f"平均速率:     {self.stats['total']/(self.stats['total_time'] or 1):.2f} contracts/s")
        
        if self.stats['total_nodes_before'] > 0:
            reduction = (1 - self.stats['total_nodes_after'] / self.stats['total_nodes_before']) * 100
            print(f"\n🎯 节点优化统计:")
            print(f"优化前节点总数: {self.stats['total_nodes_before']}")
            print(f"优化后节点总数: {self.stats['total_nodes_after']}")
            print(f"节点减少率:     {reduction:.1f}%")
        
        print(f"\n📁 输出目录: {self.output_dir}")
        print(f"{'='*60}")
    
    def save_error_log(self):
        """保存错误日志"""
        error_log = self.output_dir / "errors.log"
        
        with open(error_log, 'w', encoding='utf-8') as f:
            f.write(f"批量处理错误日志\n")
            f.write(f"{'='*60}\n")
            f.write(f"总错误数: {len(self.errors)}\n\n")
            
            for line_no, error in self.errors:
                f.write(f"行号 {line_no}: {error}\n")
        
        print(f"⚠️  错误日志已保存: {error_log}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='批量处理Solidity合约生成DFG',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用标准模式处理
  python batch_process.py data/ponzi_code_dataset_small_1514.json output/batch_dfgs
  
  # 使用紧凑模式处理
  python batch_process.py data/ponzi_code_dataset_small_1514.json output/batch_dfgs --mode compact
  
  # 使用详细模式处理
  python batch_process.py data/ponzi_code_dataset_small_1514.json output/batch_dfgs --mode verbose
        """
    )
    
    parser.add_argument('input_file', help='输入JSONL文件路径')
    parser.add_argument('output_dir', help='输出目录路径')
    parser.add_argument(
        '--mode',
        choices=['compact', 'standard', 'verbose'],
        default='standard',
        help='DFG输出模式 (默认: standard)'
    )
    parser.add_argument(
        '--progress',
        type=int,
        default=100,
        help='进度显示间隔 (默认: 每100个合约)'
    )
    
    args = parser.parse_args()
    
    # 转换模式
    mode_map = {
        'compact': OutputMode.COMPACT,
        'standard': OutputMode.STANDARD,
        'verbose': OutputMode.VERBOSE
    }
    mode = mode_map[args.mode]
    
    # 创建处理器并执行
    processor = BatchProcessor(args.input_file, args.output_dir, mode)
    processor.process_all(progress_interval=args.progress)


if __name__ == '__main__':
    main()
