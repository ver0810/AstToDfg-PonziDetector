"""
JSON序列化器模块
将DFG序列化为JSON格式并保存到文件
"""

import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .node_types import DFG, DFGNode, DFGEdge, EdgeType
from .dfg_config import DFGConfig


class JSONSerializer:
    """JSON序列化器"""
    
    def __init__(self, config: Optional[DFGConfig] = None, indent: int = 2):
        """初始化序列化器"""
        self.config = config or DFGConfig.standard()
        self.indent = indent
    
    def serialize_dfg(self, dfg: DFG) -> Dict[str, Any]:
        """将DFG序列化为字典"""
        if not dfg:
            return {}
        
        serialized = {
            "contract": dfg.contract_name,
            "solidity_version": dfg.solidity_version,
            "nodes": self._serialize_nodes(dfg.nodes),
            "edges": self._serialize_edges(dfg.edges),
            "metadata": self._serialize_metadata(dfg)
        }
        
        # 添加入口节点信息
        if dfg.entry_node_id:
            serialized["entry_node_id"] = dfg.entry_node_id
        
        return serialized
    
    def _serialize_nodes(self, nodes: Dict[str, DFGNode]) -> Dict[str, Any]:
        """序列化节点"""
        serialized_nodes = {}
        
        for node_id, node in nodes.items():
            serialized_node = {
                "id": node.node_id,
                "type": node.node_type,
                "name": node.name,
                "data_type": node.data_type,
                "scope": node.scope,
                "source_location": self._serialize_source_location(node.ast_node),
                "properties": node.properties or {}
            }
            
            # 根据配置决定是否添加文本
            if self.config.include_node_text and hasattr(node.ast_node, 'text') and node.ast_node.text:
                text = node.ast_node.text
                # 应用文本长度限制
                if self.config.text_max_length > 0 and len(text) > self.config.text_max_length:
                    text = text[:self.config.text_max_length] + "..."
                serialized_node["text"] = text
            
            # 根据配置决定是否添加AST元数据
            if self.config.include_ast_metadata and hasattr(node.ast_node, 'metadata') and node.ast_node.metadata:
                serialized_node["ast_metadata"] = node.ast_node.metadata
            
            serialized_nodes[node_id] = serialized_node
        
        return serialized_nodes
    
    def _serialize_edges(self, edges: Dict[str, DFGEdge]) -> Dict[str, Any]:
        """序列化边"""
        serialized_edges = {}
        
        for edge_id, edge in edges.items():
            serialized_edge = {
                "id": edge.edge_id,
                "source": edge.source_node_id,
                "target": edge.target_node_id,
                "type": edge.edge_type.value,
                "label": edge.label,
                "weight": edge.weight,
                "properties": edge.properties or {}
            }
            
            serialized_edges[edge_id] = serialized_edge
        
        return serialized_edges
    
    def _serialize_source_location(self, ast_node) -> Optional[Dict[str, Any]]:
        """序列化源码位置信息"""
        if not hasattr(ast_node, 'source_location') or not ast_node.source_location:
            return None
        
        loc = ast_node.source_location
        return {
            "line": loc.line,
            "column": loc.column,
            "end_line": loc.end_line,
            "end_column": loc.end_column
        }
    
    def _serialize_metadata(self, dfg: DFG) -> Dict[str, Any]:
        """序列化元数据"""
        metadata = dfg.metadata.copy() if dfg.metadata else {}
        
        # 添加统计信息
        metadata.update({
            "generated_at": datetime.now().isoformat(),
            "node_count": len(dfg.nodes),
            "edge_count": len(dfg.edges),
            "serializer_version": "1.0.0"
        })
        
        # 添加边类型统计
        edge_type_counts = {}
        for edge in dfg.edges.values():
            edge_type = edge.edge_type.value
            edge_type_counts[edge_type] = edge_type_counts.get(edge_type, 0) + 1
        metadata["edge_type_distribution"] = edge_type_counts
        
        # 添加节点类型统计
        node_type_counts = {}
        for node in dfg.nodes.values():
            node_type = node.node_type
            node_type_counts[node_type] = node_type_counts.get(node_type, 0) + 1
        metadata["node_type_distribution"] = node_type_counts
        
        return metadata
    
    def save_to_file(self, dfg: DFG, file_path: str, ensure_dir: bool = True) -> bool:
        """将DFG保存到JSON文件"""
        try:
            # 确保目录存在
            if ensure_dir:
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 序列化DFG
            serialized_dfg = self.serialize_dfg(dfg)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serialized_dfg, f, indent=self.indent, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"Error saving DFG to file {file_path}: {e}")
            return False
    
    def load_from_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """从JSON文件加载DFG数据"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        except Exception as e:
            print(f"Error loading DFG from file {file_path}: {e}")
            return None
    
    def serialize_multiple_dfgs(self, dfgs: Dict[str, DFG]) -> Dict[str, Any]:
        """序列化多个DFG"""
        serialized = {
            "contracts": {},
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "contract_count": len(dfgs),
                "serializer_version": "1.0.0"
            }
        }
        
        for contract_name, dfg in dfgs.items():
            serialized["contracts"][contract_name] = self.serialize_dfg(dfg)
        
        return serialized
    
    def save_multiple_dfgs(self, dfgs: Dict[str, DFG], file_path: str, ensure_dir: bool = True) -> bool:
        """保存多个DFG到单个JSON文件"""
        try:
            # 确保目录存在
            if ensure_dir:
                Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 序列化多个DFG
            serialized_dfgs = self.serialize_multiple_dfgs(dfgs)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serialized_dfgs, f, indent=self.indent, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"Error saving multiple DFGs to file {file_path}: {e}")
            return False
    
    def export_summary(self, dfg: DFG, file_path: str) -> bool:
        """导出DFG摘要信息"""
        try:
            summary = {
                "contract": dfg.contract_name,
                "solidity_version": dfg.solidity_version,
                "statistics": {
                    "total_nodes": len(dfg.nodes),
                    "total_edges": len(dfg.edges),
                    "entry_node": dfg.entry_node_id
                },
                "node_types": {},
                "edge_types": {},
                "functions": [],
                "state_variables": []
            }
            
            # 统计节点类型
            for node in dfg.nodes.values():
                node_type = node.node_type
                summary["node_types"][node_type] = summary["node_types"].get(node_type, 0) + 1
                
                # 收集函数信息
                if node_type in ["function", "constructor_function"]:
                    func_info = {
                        "name": node.name,
                        "scope": node.scope,
                        "data_type": node.data_type
                    }
                    summary["functions"].append(func_info)
                
                # 收集状态变量信息
                elif node_type == "state_variable":
                    var_info = {
                        "name": node.name,
                        "data_type": node.data_type,
                        "scope": node.scope
                    }
                    summary["state_variables"].append(var_info)
            
            # 统计边类型
            for edge in dfg.edges.values():
                edge_type = edge.edge_type.value
                summary["edge_types"][edge_type] = summary["edge_types"].get(edge_type, 0) + 1
            
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=self.indent, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"Error exporting DFG summary to file {file_path}: {e}")
            return False
    
    def validate_serialized_dfg(self, data: Dict[str, Any]) -> bool:
        """验证序列化的DFG数据格式"""
        required_fields = ["contract", "solidity_version", "nodes", "edges"]
        
        for field in required_fields:
            if field not in data:
                print(f"Missing required field: {field}")
                return False
        
        # 验证节点格式
        for node_id, node in data["nodes"].items():
            if not isinstance(node, dict):
                print(f"Node {node_id} is not a dictionary")
                return False
            
            required_node_fields = ["id", "type"]
            for field in required_node_fields:
                if field not in node:
                    print(f"Node {node_id} missing required field: {field}")
                    return False
        
        # 验证边格式
        for edge_id, edge in data["edges"].items():
            if not isinstance(edge, dict):
                print(f"Edge {edge_id} is not a dictionary")
                return False
            
            required_edge_fields = ["id", "source", "target", "type"]
            for field in required_edge_fields:
                if field not in edge:
                    print(f"Edge {edge_id} missing required field: {field}")
                    return False
        
        return True