#!/usr/bin/env python3
"""
主调度脚本 - AST-Solidity 流水线入口
功能：源代码 -> AST -> DFG -> 检测 -> 结果（可选可视化）

优化版本:
- 支持配置文件管理
- 支持数据集批量处理
- 增强的检测功能(缓存、并发控制)
- Result类型的函数式错误处理
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import time
from datetime import datetime

from .analyzer import SolidityAnalyzer
from .dfg_builder.dfg_config import DFGConfig, OutputMode
from .visualization.visualizer import DFGVisualizer
from .detector.llm_detector import PonziDetectionPipeline, LLMConfig
from .utils.config_manager import PipelineConfig, LLMProviderConfig
from .utils.dataset_loader import DatasetLoader, ContractEntry
from .utils.result import Result


class SolidityPipeline:
    """Solidity 智能合约分析流水线（增强版）"""
    
    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        solidity_version: Optional[str] = None,
        output_dir: Optional[str] = None,
        dfg_mode: Optional[OutputMode] = None,
        enable_detection: Optional[bool] = None,
        enable_visualization: Optional[bool] = None,
        llm_config: Optional[LLMConfig] = None
    ):
        """
        初始化流水线
        
        Args:
            config: 完整配置对象（优先级最高）
            solidity_version: Solidity版本（向后兼容）
            output_dir: 输出目录（向后兼容）
            dfg_mode: DFG输出模式（向后兼容）
            enable_detection: 是否启用庞氏骗局检测（向后兼容）
            enable_visualization: 是否启用DFG可视化（向后兼容）
            llm_config: LLM配置（向后兼容）
        """
        # 使用配置对象或创建默认配置
        if config is None:
            config = PipelineConfig()
            
            # 应用向后兼容参数
            if solidity_version:
                config.solidity_version = solidity_version
            if output_dir:
                config.output.output_dir = output_dir
            if dfg_mode:
                config.dfg.mode = dfg_mode.value if hasattr(dfg_mode, 'value') else str(dfg_mode)
            if enable_detection is not None:
                config.detection.enabled = enable_detection
            if llm_config:
                config.detection.provider = LLMProviderConfig(
                    api_key=llm_config.api_key,
                    base_url=llm_config.base_url,
                    model=llm_config.model
                )
        
        self.config = config
        self.enable_visualization = enable_visualization if enable_visualization is not None else False
        
        # 创建输出目录
        self.output_dir = Path(config.output.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化DFG配置
        mode_map = {
            'compact': DFGConfig.compact(),
            'standard': DFGConfig.standard(),
            'verbose': DFGConfig.verbose()
        }
        self.dfg_config = mode_map.get(config.dfg.mode, DFGConfig.standard())
        
        # 初始化分析器
        self.analyzer = SolidityAnalyzer(
            solidity_version=config.solidity_version,
            output_dir=str(self.output_dir),
            dfg_config=self.dfg_config
        )
        
        # 初始化可视化器（如果需要）
        self.visualizer = DFGVisualizer() if self.enable_visualization else None
        
        # 初始化检测器（如果需要）
        if config.detection.enabled:
            llm_cfg = LLMConfig(
                api_key=config.detection.provider.api_key or "",
                base_url=config.detection.provider.base_url or "",
                model=config.detection.provider.model or ""
            )
            self.detector = PonziDetectionPipeline(config=llm_cfg)
        else:
            self.detector = None
    
    def process_file(self, source_file: Path, contract_name: Optional[str] = None, 
                    label: Optional[int] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理单个Solidity源文件

        Args:
            source_file: 源文件路径
            contract_name: 合约名称（可选，默认使用文件名）
            label: 数据集标签（可选，0=合法，1=庞氏骗局）
            metadata: 额外的元数据（可选）

        Returns:
            处理结果字典
        """
        if contract_name is None:
            contract_name = source_file.stem

        print(f"\n{'='*70}")
        print(f"处理合约: {contract_name}")
        print(f"源文件: {source_file}")
        print(f"{'='*70}")

        result = {
            "contract_name": contract_name,
            "source_file": str(source_file),
            "timestamp": datetime.now().isoformat(),
            "steps": {}
        }

        try:
            # 步骤1: 读取源代码
            print("\n[1/5] 读取源代码...")
            start_time = time.time()
            with open(source_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
            result["steps"]["read_source"] = {
                "status": "success",
                "time": time.time() - start_time,
                "code_length": len(source_code)
            }
            print(f"    ✅ 读取成功 ({len(source_code)} 字符)")

            # 步骤2: 构建AST
            print("\n[2/5] 构建AST...")
            start_time = time.time()
            
            # 准备额外的元数据
            extra_metadata = {}
            if label is not None:
                extra_metadata['label'] = label
            if metadata:
                extra_metadata.update(metadata)
            
            # 调用 analyze_source 方法，禁用内置的JSON和可视化生成
            analysis_result = self.analyzer.analyze_source(
                source_code,
                contract_name,
                generate_json=True,
                generate_visualization=False,  # 我们后面会自己生成
                generate_summary=False,
                extra_metadata=extra_metadata if extra_metadata else None
            )

            if not analysis_result.get("success", False):
                error_msg = analysis_result.get("error", "Unknown error")
                result["steps"]["build_ast"] = {
                    "status": "failed",
                    "error": error_msg,
                    "time": time.time() - start_time
                }
                print(f"    ❌ AST构建失败: {error_msg}")
                result["status"] = "failed"
                result["error"] = error_msg
                return result

            result["steps"]["build_ast"] = {
                "status": "success",
                "time": time.time() - start_time,
                "ast_nodes": analysis_result.get("ast_nodes", 0)
            }
            print(f"    ✅ AST构建成功")
            print(f"       AST节点数: {analysis_result.get('ast_nodes', 0)}")

            # 步骤3: 构建DFG
            print("\n[3/5] 构建DFG...")
            start_time = time.time()
            dfg_json_path = analysis_result.get("json_file")

            if dfg_json_path and Path(dfg_json_path).exists():
                result["steps"]["build_dfg"] = {
                    "status": "success",
                    "time": time.time() - start_time,
                    "output_file": str(dfg_json_path),
                    "node_count": analysis_result.get("dfg_nodes", 0),
                    "edge_count": analysis_result.get("dfg_edges", 0),
                    "filtered_nodes": analysis_result.get("filtered_nodes", 0),
                    "filtered_edges": analysis_result.get("filtered_edges", 0)
                }
                print(f"    ✅ DFG构建成功")
                print(f"       节点数: {analysis_result.get('dfg_nodes', 0)}")
                print(f"       边数: {analysis_result.get('dfg_edges', 0)}")
                print(f"       过滤节点: {analysis_result.get('filtered_nodes', 0)}")
                print(f"       输出: {dfg_json_path}")
            else:
                result["steps"]["build_dfg"] = {
                    "status": "failed",
                    "error": "DFG构建失败"
                }
                print(f"    ❌ DFG构建失败")
                return result

            # 步骤4: 庞氏骗局检测（可选）
            if self.config.detection.enabled and self.detector:
                print("\n[4/5] 执行庞氏骗局检测...")
                start_time = time.time()
                try:
                    # 读取DFG JSON进行检测
                    import asyncio
                    detection_result = asyncio.run(
                        self.detector.detect_from_json_file(str(dfg_json_path))
                    )

                    result["steps"]["detection"] = {
                        "status": "success",
                        "time": time.time() - start_time,
                        "result": detection_result
                    }

                    # 保存检测结果
                    detection_output = self.output_dir / f"{contract_name}_detection.json"
                    with open(detection_output, 'w', encoding='utf-8') as f:
                        json.dump(detection_result, f, indent=2, ensure_ascii=False)

                    classification = detection_result.get("classification_result", {})
                    print(f"    ✅ 检测完成")
                    print(f"       是否为庞氏骗局: {classification.get('is_ponzi', False)}")
                    print(f"       置信度: {classification.get('confidence', 0.0):.2f}")
                    print(f"       风险等级: {classification.get('risk_level', '未知')}")
                    print(f"       结果保存至: {detection_output}")

                except Exception as e:
                    result["steps"]["detection"] = {
                        "status": "failed",
                        "error": str(e),
                        "time": time.time() - start_time
                    }
                    print(f"    ❌ 检测失败: {e}")
            else:
                print("\n[4/5] 跳过检测（未启用）")
                result["steps"]["detection"] = {"status": "skipped"}

            # 步骤5: 可视化（可选）
            if self.enable_visualization and self.visualizer:
                print("\n[5/5] 生成DFG可视化...")
                start_time = time.time()
                try:
                    viz_output = self.output_dir / f"{contract_name}_dfg"
                    success = self.visualizer.visualize_from_json(
                        str(dfg_json_path),
                        str(viz_output)
                    )
                    if success:
                        result["steps"]["visualization"] = {
                            "status": "success",
                            "time": time.time() - start_time,
                            "output_file": f"{viz_output}.png"
                        }
                        print(f"    ✅ 可视化完成")
                        print(f"       输出: {viz_output}.png")
                    else:
                        result["steps"]["visualization"] = {
                            "status": "failed",
                            "error": "可视化生成失败",
                            "time": time.time() - start_time
                        }
                        print(f"    ❌ 可视化失败")
                except Exception as e:
                    result["steps"]["visualization"] = {
                        "status": "failed",
                        "error": str(e),
                        "time": time.time() - start_time
                    }
                    print(f"    ❌ 可视化失败: {e}")
            else:
                print("\n[5/5] 跳过可视化（未启用）")
                result["steps"]["visualization"] = {"status": "skipped"}

            result["status"] = "success"

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            print(f"\n❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()

        return result

    def process_batch(self, source_files: List[Path]) -> Dict[str, Any]:
        """
        批量处理多个Solidity源文件

        Args:
            source_files: 源文件路径列表

        Returns:
            批处理结果字典
        """
        print(f"\n{'='*70}")
        print(f"批量处理模式")
        print(f"文件总数: {len(source_files)}")
        print(f"{'='*70}")

        batch_result = {
            "total_files": len(source_files),
            "timestamp": datetime.now().isoformat(),
            "results": [],
            "summary": {
                "success": 0,
                "failed": 0,
                "total_time": 0
            }
        }

        start_time = time.time()

        for i, source_file in enumerate(source_files, 1):
            print(f"\n进度: [{i}/{len(source_files)}]")
            result = self.process_file(source_file)
            batch_result["results"].append(result)

            if result["status"] == "success":
                batch_result["summary"]["success"] += 1
            else:
                batch_result["summary"]["failed"] += 1

        batch_result["summary"]["total_time"] = time.time() - start_time

        # 保存批处理结果
        batch_output = self.output_dir / f"batch_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(batch_output, 'w', encoding='utf-8') as f:
            json.dump(batch_result, f, indent=2, ensure_ascii=False)

        # 打印总结
        print(f"\n{'='*70}")
        print(f"批处理完成")
        print(f"{'='*70}")
        print(f"总文件数: {batch_result['total_files']}")
        print(f"成功: {batch_result['summary']['success']}")
        print(f"失败: {batch_result['summary']['failed']}")
        print(f"总耗时: {batch_result['summary']['total_time']:.2f}秒")
        print(f"结果保存至: {batch_output}")
        print(f"{'='*70}")
        
        return batch_result
    
    def process_dataset(self, dataset_path: str, limit: Optional[int] = None) -> Result[Dict[str, Any]]:
        """
        从数据集文件批量处理合约
        
        Args:
            dataset_path: 数据集文件路径（JSON格式）
            limit: 可选的处理数量限制
            
        Returns:
            Result包含处理结果字典
        """
        print(f"\n{'='*70}")
        print(f"数据集处理模式")
        print(f"数据集文件: {dataset_path}")
        if limit:
            print(f"限制数量: {limit}")
        print(f"{'='*70}")
        
        # 加载数据集
        load_result = DatasetLoader.load_json_dataset(dataset_path)
        if load_result.is_failure:
            print(f"❌ 加载数据集失败: {load_result.error}")
            return Result.failure(load_result.error)
        
        entries = load_result.value
        
        # 应用限制
        if limit and limit > 0:
            entries = entries[:limit]
        
        print(f"\n将处理 {len(entries)} 个合约...")
        
        batch_result = {
            "dataset": dataset_path,
            "total_entries": len(entries),
            "timestamp": datetime.now().isoformat(),
            "results": [],
            "summary": {
                "success": 0,
                "failed": 0,
                "total_time": 0
            }
        }
        
        start_time = time.time()
        
        for i, entry in enumerate(entries, 1):
            contract_name = f"contract_{entry.index}"
            if entry.metadata and 'file_name' in entry.metadata:
                contract_name = entry.metadata['file_name'].replace('.sol', '')
            
            print(f"\n进度: [{i}/{len(entries)}] 处理 {contract_name}...")
            
            try:
                # 将代码写入临时文件
                temp_file = self.output_dir / f"temp_{contract_name}.sol"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(entry.code)
                
                # 处理文件，传递label和metadata
                result = self.process_file(temp_file, contract_name, 
                                          label=entry.label, 
                                          metadata=entry.metadata)
                
                # 添加标签到结果（用于批处理报告）
                if entry.label is not None:
                    result["label"] = entry.label
                if entry.metadata:
                    result["metadata"] = entry.metadata
                
                batch_result["results"].append(result)
                
                if result["status"] == "success":
                    batch_result["summary"]["success"] += 1
                    print(f"  ✅ 成功")
                else:
                    batch_result["summary"]["failed"] += 1
                    print(f"  ❌ 失败: {result.get('error', 'Unknown error')}")
                
                # 清理临时文件
                if temp_file.exists():
                    temp_file.unlink()
                    
            except Exception as e:
                error_result = {
                    "contract_name": contract_name,
                    "status": "failed",
                    "error": str(e),
                    "label": entry.label
                }
                batch_result["results"].append(error_result)
                batch_result["summary"]["failed"] += 1
                print(f"  ❌ 异常: {e}")
        
        batch_result["summary"]["total_time"] = time.time() - start_time
        
        # 保存批处理结果
        batch_output = self.output_dir / f"dataset_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(batch_output, 'w', encoding='utf-8') as f:
            json.dump(batch_result, f, indent=2, ensure_ascii=False)
        
        # 打印总结
        print(f"\n{'='*70}")
        print(f"数据集处理完成")
        print(f"{'='*70}")
        print(f"总条目数: {batch_result['total_entries']}")
        print(f"成功: {batch_result['summary']['success']}")
        print(f"失败: {batch_result['summary']['failed']}")
        print(f"总耗时: {batch_result['summary']['total_time']:.2f}秒")
        print(f"结果保存至: {batch_output}")
        print(f"{'='*70}")
        
        return Result.success(batch_result)
def main():
    """主函数 - 命令行入口"""
    parser = argparse.ArgumentParser(
        description="Solidity 智能合约分析流水线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 分析单个合约文件
  python -m src.main contract.sol
  
  # 从配置文件加载设置
  python -m src.main contract.sol --config config.json
  
  # 处理JSON数据集
  python -m src.main --dataset data.json
  python -m src.main --dataset data.json --limit 100

  # 分析并检测庞氏骗局
  python -m src.main contract.sol --detect
  
  # 批量检测已生成的JSON文件
  python -m src.main --detect-only --detect-dir output

  # 分析、检测并可视化
  python -m src.main contract.sol --detect --visualize

  # 批量处理多个文件
  python -m src.main file1.sol file2.sol file3.sol --batch

  # 使用紧凑模式输出
  python -m src.main contract.sol --mode compact

  # 指定LLM提供商
  python -m src.main contract.sol --detect --llm-provider deepseek
        """
    )

    # 基本参数
    parser.add_argument(
        'files',
        nargs='*',  # 改为可选，支持 --dataset 模式
        type=str,
        help='Solidity源文件路径（支持多个文件）'
    )
    
    # 数据集参数
    parser.add_argument(
        '--dataset',
        type=str,
        help='JSON数据集文件路径'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='限制处理的合约数量'
    )
    
    # 配置文件
    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径（JSON格式）'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default='output',
        help='输出目录（默认: output）'
    )

    parser.add_argument(
        '--solidity-version',
        type=str,
        default='0.4.x',
        choices=['0.4.x', '0.5.x', '0.6.x', '0.7.x', '0.8.x'],
        help='Solidity版本（默认: 0.4.x）'
    )

    # DFG配置
    parser.add_argument(
        '-m', '--mode',
        type=str,
        default='standard',
        choices=['compact', 'standard', 'verbose'],
        help='DFG输出模式（默认: standard）'
    )

    # 功能开关
    parser.add_argument(
        '-d', '--detect',
        action='store_true',
        help='启用庞氏骗局检测'
    )
    
    parser.add_argument(
        '--detect-only',
        action='store_true',
        help='仅运行检测，不生成DFG（需要已有JSON文件）'
    )
    
    parser.add_argument(
        '--detect-dir',
        type=str,
        default='output',
        help='检测模式的输入目录（默认: output）'
    )
    
    parser.add_argument(
        '--detect-pattern',
        type=str,
        default='*.json',
        help='检测模式的文件模式（默认: *.json）'
    )

    parser.add_argument(
        '--visualize',
        action='store_true',
        help='启用DFG可视化'
    )

    parser.add_argument(
        '-b', '--batch',
        action='store_true',
        help='批量处理模式'
    )

    # LLM配置（用于检测）
    parser.add_argument(
        '--llm-provider',
        type=str,
        choices=['qwen', 'deepseek', 'openai'],
        default='qwen',
        help='LLM提供商（默认: qwen）'
    )
    
    parser.add_argument(
        '--api-key',
        type=str,
        help='LLM API密钥（默认从环境变量读取）'
    )

    parser.add_argument(
        '--base-url',
        type=str,
        help='LLM API基础URL（默认从环境变量读取）'
    )

    parser.add_argument(
        '--model',
        type=str,
        help='LLM模型名称（默认从环境变量读取）'
    )
    
    parser.add_argument(
        '--concurrency',
        type=int,
        default=40,
        help='批量检测并发数（默认: 40）'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='禁用检测结果缓存'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='详细输出模式'
    )

    args = parser.parse_args()
    
    # 检测仅检测模式
    if args.detect_only:
        import asyncio
        from .detector.batch_detector import BatchDetector
        
        print("\n🔍 仅检测模式 - 处理已有JSON文件")
        
        # 从配置或参数创建LLM配置
        if args.config:
            config = PipelineConfig.load_from_file(args.config)
            config = PipelineConfig.load_from_args(args)
        else:
            config = PipelineConfig.load_from_args(args)
            config.detection.enabled = True
        
        llm_config = LLMConfig(
            api_key=config.detection.provider.api_key or "",
            base_url=config.detection.provider.base_url or "",
            model=config.detection.provider.model or ""
        )
        
        detector = BatchDetector(
            config=llm_config,
            concurrency_limit=args.concurrency,
            cache_dir="cache",
            enable_cache=not args.no_cache
        )
        
        async def run_detection():
            stats = await detector.detect_batch(
                output_dir=args.detect_dir,
                pattern=args.detect_pattern,
                limit=args.limit
            )
            detector.print_statistics(stats)
            detector.save_results(stats)
            return stats['successful'] > 0
        
        success = asyncio.run(run_detection())
        sys.exit(0 if success else 1)
    
    # 数据集处理模式
    if args.dataset:
        # 加载配置
        if args.config:
            config = PipelineConfig.load_from_file(args.config)
            config = PipelineConfig.load_from_args(args)
        else:
            config = PipelineConfig.load_from_args(args)
        
        # 创建流水线
        pipeline = SolidityPipeline(config=config)
        
        # 处理数据集
        result = pipeline.process_dataset(args.dataset, args.limit)
        
        if result.is_success:
            summary = result.value["summary"]
            sys.exit(0 if summary["success"] > 0 else 1)
        else:
            print(f"\n❌ 数据集处理失败: {result.error}")
            sys.exit(1)
    
    # 常规文件处理模式
    if not args.files:
        print("错误: 请提供Solidity源文件或使用 --dataset 参数")
        sys.exit(1)
    
    # 加载配置
    if args.config:
        config = PipelineConfig.load_from_file(args.config)
        config = PipelineConfig.load_from_args(args)
    else:
        config = PipelineConfig.load_from_args(args)
    
    # 初始化流水线
    pipeline = SolidityPipeline(config=config, enable_visualization=args.visualize)

    # 处理文件
    source_files = [Path(f) for f in args.files]

    # 验证文件存在
    for f in source_files:
        if not f.exists():
            print(f"❌ 文件不存在: {f}")
            sys.exit(1)

    # 批量模式或单文件模式
    if args.batch or len(source_files) > 1:
        result = pipeline.process_batch(source_files)
        # 批量处理的成功判断
        if result.get("summary", {}).get("success", 0) > 0:
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        result = pipeline.process_file(source_files[0])
        # 单文件处理的成功判断
        if result.get("status") == "success":
            sys.exit(0)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
