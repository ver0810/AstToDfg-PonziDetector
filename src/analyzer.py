"""
主分析器模块
整合AST构建、DFG构建、序列化和可视化功能
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import json


class SolidityAnalyzer:
    """Solidity代码分析器"""
    
    def __init__(self, solidity_version: str = "0.4.x", 
                 output_dir: str = "output",
                 dfg_config: Optional[Any] = None):
        """
        初始化分析器
        
        Args:
            solidity_version: Solidity版本
            output_dir: 输出目录
            dfg_config: DFG配置对象（DFGConfig实例），如果为None则使用默认配置
        """
        self.solidity_version = solidity_version
        self.output_dir = Path(output_dir)
        self.dfg_config = dfg_config
        
        # 组件初始化状态
        self.components_ready = False
        self._init_components()
        
        # 分析结果
        self.analysis_results: Dict[str, Any] = {}
    
    def _init_components(self) -> None:
        """初始化组件"""
        try:
            from .ast_builder.ast_builder import ASTBuilder
            from .dfg_builder.dfg_builder import DFGBuilder
            from .json_serializer import JSONSerializer
            from .visualization.visualizer import DFGVisualizer
            from .ast_builder.solidity_04x_handler import Solidity04xHandler
            from .ast_builder.node_types import ASTNode, DFG, ContractNode
            from .dfg_builder.dfg_config import DFGConfig
            
            # 如果没有提供配置，使用标准配置
            if self.dfg_config is None:
                self.dfg_config = DFGConfig.standard()
            
            # 初始化组件（传入配置）
            self.ast_builder = ASTBuilder()
            self.dfg_builder = DFGBuilder(self.solidity_version, self.dfg_config)
            self.json_serializer = JSONSerializer(self.dfg_config)
            self.visualizer = DFGVisualizer()
            
            # 0.4.x特性处理器
            self.legacy_handler = Solidity04xHandler() if self.solidity_version.startswith("0.4") else None
            
            # 保存类型引用
            self.ASTNode = ASTNode
            self.DFG = DFG
            self.ContractNode = ContractNode
            self.DFGConfig = DFGConfig
            
            self.components_ready = True
            
        except ImportError as e:
            print(f"Warning: Failed to import components: {e}")
            self.components_ready = False
            self.ast_builder = None
            self.dfg_builder = None
            self.json_serializer = None
            self.visualizer = None
            self.legacy_handler = None
            self.ASTNode = None
            self.DFG = None
            self.ContractNode = None
            self.DFGConfig = None
    
    def analyze_file(self, file_path: str, 
                    generate_json: bool = True,
                    generate_visualization: bool = True,
                    generate_summary: bool = True) -> Dict[str, Any]:
        """分析单个Solidity文件"""
        if not self.components_ready:
            return {
                "file": file_path,
                "error": "Components not properly initialized",
                "success": False
            }
        
        try:
            # 读取源码
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            return self.analyze_source(source_code, Path(file_path).stem, 
                                     generate_json, generate_visualization, generate_summary)
        
        except Exception as e:
            error_result = {
                "file": file_path,
                "error": str(e),
                "success": False
            }
            print(f"Error analyzing file {file_path}: {e}")
            return error_result
    
    def analyze_source(self, source_code: str, contract_name: str = "Unknown",
                      generate_json: bool = True,
                      generate_visualization: bool = True,
                      generate_summary: bool = True,
                      extra_metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        分析Solidity源码
        
        Args:
            source_code: 源代码
            contract_name: 合约名称
            generate_json: 是否生成JSON文件
            generate_visualization: 是否生成可视化
            generate_summary: 是否生成摘要
            extra_metadata: 额外的元数据（如label等），将添加到JSON文件中
            
        Returns:
            分析结果字典
        """
        if not self.components_ready:
            return {
                "contract": contract_name,
                "error": "Components not properly initialized",
                "success": False
            }
        
        try:
            # 构建AST
            ast_root = self.ast_builder.build_ast(source_code)
            if not ast_root:
                return {
                    "contract": contract_name,
                    "error": "Failed to build AST",
                    "success": False
                }
            
            # 提取合约名称
            actual_contract_name = self._extract_contract_name(ast_root) or contract_name
            
            # 处理0.4.x特性
            if self.legacy_handler:
                self._process_legacy_features(ast_root)
            
            # 构建DFG
            dfg = self.dfg_builder.build_dfg(ast_root, actual_contract_name)
            if not dfg:
                return {
                    "contract": actual_contract_name,
                    "error": "Failed to build DFG",
                    "success": False
                }
            
            # 生成输出文件
            ast_node_count = self._count_ast_nodes(ast_root)
            result = {
                "contract": actual_contract_name,
                "solidity_version": self.solidity_version,
                "success": True,
                "ast_nodes": ast_node_count,
                "dfg_nodes": len(dfg.nodes),
                "dfg_edges": len(dfg.edges),
                "filtered_nodes": self.dfg_builder.filtered_nodes_count,
                "filtered_edges": self.dfg_builder.filtered_edges_count,
                "optimization_stats": {
                    "original_potential_nodes": ast_node_count,
                    "kept_nodes": len(dfg.nodes),
                    "filtered_nodes": self.dfg_builder.filtered_nodes_count,
                    "reduction_rate": f"{(self.dfg_builder.filtered_nodes_count / max(ast_node_count, 1) * 100):.1f}%"
                }
            }
            
            # 生成JSON文件
            if generate_json:
                json_path = self.output_dir / "dfgs" / f"{actual_contract_name}_dfg.json"
                if self.json_serializer.save_to_file(dfg, str(json_path), extra_metadata=extra_metadata):
                    result["json_file"] = str(json_path)
                
                # 生成摘要
                if generate_summary:
                    summary_path = self.output_dir / "dfgs" / f"{actual_contract_name}_summary.json"
                    if self.json_serializer.export_summary(dfg, str(summary_path)):
                        result["summary_file"] = str(summary_path)
            
            # 生成可视化
            if generate_visualization:
                viz_path = self.output_dir / "graphs" / f"{actual_contract_name}_dfg"
                if self.visualizer.visualize_dfg(dfg, str(viz_path)):
                    result["visualization_file"] = f"{viz_path}.png"
                
                # 导出可视化统计
                viz_stats_path = self.output_dir / "graphs" / f"{actual_contract_name}_viz_stats.json"
                if self.visualizer.export_statistics(dfg, str(viz_stats_path)):
                    result["viz_stats_file"] = str(viz_stats_path)
            
            return result
        
        except Exception as e:
            return {
                "contract": contract_name,
                "error": str(e),
                "success": False
            }
    
    def analyze_directory(self, dir_path: str,
                         pattern: str = "*.sol",
                         generate_json: bool = True,
                         generate_visualization: bool = True) -> Dict[str, Any]:
        """分析目录中的所有Solidity文件"""
        dir_path_obj = Path(dir_path)
        if not dir_path_obj.exists():
            return {"error": f"Directory {dir_path} does not exist", "success": False}
        
        results = {
            "directory": str(dir_path_obj),
            "total_files": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "results": []
        }
        
        # 查找所有Solidity文件
        sol_files = list(dir_path_obj.glob(pattern))
        results["total_files"] = len(sol_files)
        
        for sol_file in sol_files:
            file_result = self.analyze_file(str(sol_file), generate_json, generate_visualization)
            results["results"].append(file_result)
            
            if file_result.get("success", False):
                results["successful_analyses"] += 1
            else:
                results["failed_analyses"] += 1
        
        # 生成整体报告
        if generate_json:
            report_path = self.output_dir / "analysis_report.json"
            self._generate_analysis_report(results, str(report_path))
            results["report_file"] = str(report_path)
        
        return results
    
    def _extract_contract_name(self, ast_root) -> Optional[str]:
        """从AST中提取合约名称"""
        if not self.ContractNode or not ast_root:
            return None
        
        if isinstance(ast_root, self.ContractNode):
            return ast_root.name
        
        # 递归查找合约节点
        if hasattr(ast_root, 'children') and ast_root.children:
            for child in ast_root.children:
                if isinstance(child, self.ContractNode):
                    return child.name
                # 递归搜索
                name = self._extract_contract_name(child)
                if name:
                    return name
        
        return None
    
    def _process_legacy_features(self, ast_root) -> None:
        """处理0.4.x特有特性"""
        if not self.legacy_handler or not ast_root:
            return
        
        # 递归处理所有节点
        self._process_node_legacy_features(ast_root)
    
    def _process_node_legacy_features(self, node) -> None:
        """递归处理节点的0.4.x特性"""
        if not node or not self.legacy_handler:
            return
        
        # 添加0.4.x元数据
        self.legacy_handler.add_legacy_metadata(node)
        
        # 处理子节点
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                self._process_node_legacy_features(child)
    
    def _count_ast_nodes(self, node) -> int:
        """递归计算AST节点数量"""
        if not node:
            return 0
        
        count = 1  # 当前节点
        if hasattr(node, 'children') and node.children:
            for child in node.children:
                count += self._count_ast_nodes(child)
        
        return count
    
    def _generate_analysis_report(self, results: Dict[str, Any], output_path: str) -> None:
        """生成分析报告"""
        report = {
            "analysis_summary": {
                "total_files": results["total_files"],
                "successful_analyses": results["successful_analyses"],
                "failed_analyses": results["failed_analyses"],
                "success_rate": results["successful_analyses"] / max(results["total_files"], 1)
            },
            "solidity_version": self.solidity_version,
            "output_directory": str(self.output_dir),
            "detailed_results": results["results"],
            "generated_at": str(Path.cwd())
        }
        
        # 统计信息
        total_nodes = 0
        total_edges = 0
        contracts = []
        
        for result in results["results"]:
            if result.get("success", False):
                total_nodes += result.get("dfg_nodes", 0)
                total_edges += result.get("dfg_edges", 0)
                contracts.append(result.get("contract", "Unknown"))
        
        report["statistics"] = {
            "total_contracts": len(contracts),
            "total_dfg_nodes": total_nodes,
            "total_dfg_edges": total_edges,
            "average_nodes_per_contract": total_nodes / max(len(contracts), 1),
            "average_edges_per_contract": total_edges / max(len(contracts), 1),
            "analyzed_contracts": contracts
        }
        
        # 保存报告
        self.output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        return {
            "analyzer_config": {
                "solidity_version": self.solidity_version,
                "output_directory": str(self.output_dir),
                "legacy_handler_enabled": self.legacy_handler is not None,
                "components_ready": self.components_ready
            },
            "components": {
                "ast_builder": type(self.ast_builder).__name__ if self.ast_builder else None,
                "dfg_builder": type(self.dfg_builder).__name__ if self.dfg_builder else None,
                "json_serializer": type(self.json_serializer).__name__ if self.json_serializer else None,
                "visualizer": type(self.visualizer).__name__ if self.visualizer else None
            }
        }
    
    def validate_setup(self) -> Dict[str, bool]:
        """验证设置是否正确"""
        validation_results = {}
        
        # 检查输出目录
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            validation_results["output_directory"] = True
        except Exception:
            validation_results["output_directory"] = False
        
        # 检查子目录
        try:
            (self.output_dir / "dfgs").mkdir(parents=True, exist_ok=True)
            (self.output_dir / "graphs").mkdir(parents=True, exist_ok=True)
            validation_results["subdirectories"] = True
        except Exception:
            validation_results["subdirectories"] = False
        
        # 检查组件初始化
        validation_results["components_ready"] = self.components_ready
        validation_results["ast_builder"] = self.ast_builder is not None
        validation_results["dfg_builder"] = self.dfg_builder is not None
        validation_results["json_serializer"] = self.json_serializer is not None
        validation_results["visualizer"] = self.visualizer is not None
        validation_results["legacy_handler"] = self.legacy_handler is not None or not self.solidity_version.startswith("0.4")
        
        return validation_results
    
    def cleanup(self) -> None:
        """清理临时文件"""
        # 这里可以添加清理逻辑
        pass