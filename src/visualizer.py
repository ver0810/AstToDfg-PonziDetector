"""
Graphviz可视化器模块
使用Graphviz将DFG可视化
"""

import graphviz
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import json

from .node_types import DFG, DFGNode, DFGEdge, EdgeType


class DFGVisualizer:
    """DFG可视化器"""
    
    def __init__(self, engine: str = "dot", format: str = "png"):
        """初始化可视化器"""
        self.engine = engine
        self.format = format
        
        # 节点样式配置
        self.node_styles = {
            "contract": {
                "shape": "box",
                "style": "rounded,filled",
                "fillcolor": "lightblue",
                "fontname": "Arial"
            },
            "function": {
                "shape": "ellipse",
                "style": "filled",
                "fillcolor": "lightgreen",
                "fontname": "Arial"
            },
            "constructor_function": {
                "shape": "doubleellipse",
                "style": "filled",
                "fillcolor": "orange",
                "fontname": "Arial"
            },
            "state_variable": {
                "shape": "note",
                "style": "filled",
                "fillcolor": "lightyellow",
                "fontname": "Arial"
            },
            "local_variable": {
                "shape": "ellipse",
                "style": "filled",
                "fillcolor": "lightgray",
                "fontname": "Arial"
            },
            "expression": {
                "shape": "circle",
                "style": "filled",
                "fillcolor": "lightpink",
                "fontname": "Arial"
            },
            "parameter": {
                "shape": "parallelogram",
                "style": "filled",
                "fillcolor": "lightcyan",
                "fontname": "Arial"
            }
        }
        
        # 边样式配置
        self.edge_styles = {
            EdgeType.DATA_DEPENDENCY: {
                "color": "black",
                "style": "solid",
                "arrowhead": "normal"
            },
            EdgeType.CONTROL_DEPENDENCY: {
                "color": "red",
                "style": "dashed",
                "arrowhead": "empty"
            },
            EdgeType.FUNCTION_CALL: {
                "color": "blue",
                "style": "dotted",
                "arrowhead": "diamond"
            },
            EdgeType.DEFINITION: {
                "color": "green",
                "style": "solid",
                "arrowhead": "tee"
            },
            EdgeType.USAGE: {
                "color": "purple",
                "style": "solid",
                "arrowhead": "normal"
            },
            EdgeType.MODIFIES: {
                "color": "darkred",
                "style": "bold",
                "arrowhead": "box"
            }
        }
    
    def visualize_dfg(self, dfg: DFG, output_path: str, 
                     show_labels: bool = True, 
                     cluster_scopes: bool = True) -> bool:
        """可视化DFG"""
        try:
            # 创建Graphviz图
            dot = graphviz.Digraph(comment=f'DFG of {dfg.contract_name}',
                                 engine=self.engine,
                                 format=self.format)
            
            # 设置图属性
            dot.attr(rankdir='TB', splines='ortho', nodesep='0.8', ranksep='1.0')
            
            # 添加节点
            self._add_nodes(dot, dfg, show_labels)
            
            # 添加边
            self._add_edges(dot, dfg, show_labels)
            
            # 如果需要，按作用域聚类
            if cluster_scopes:
                dot = self._create_clustered_graph(dfg, show_labels)
            
            # 渲染图
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            if isinstance(dot, graphviz.Digraph):
                dot.render(str(output_file.with_suffix('')), cleanup=True)
            else:
                # 如果是聚类图，需要特殊处理
                dot.render(str(output_file.with_suffix('')), cleanup=True)
            
            return True
        
        except Exception as e:
            print(f"Error visualizing DFG: {e}")
            return False
    
    def visualize_from_json(self, json_file: str, output_path: str,
                           show_labels: bool = True,
                           cluster_scopes: bool = True) -> bool:
        """从JSON文件加载并可视化DFG"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 创建虚拟DFG对象
            dfg = self._create_dfg_from_json(data)
            
            return self.visualize_dfg(dfg, output_path, show_labels, cluster_scopes)
        
        except Exception as e:
            print(f"Error visualizing DFG from JSON: {e}")
            return False
    
    def _add_nodes(self, dot: graphviz.Digraph, dfg: DFG, show_labels: bool) -> None:
        """添加节点到图中"""
        for node_id, node in dfg.nodes.items():
            # 获取节点样式
            style = self.node_styles.get(node.node_type, self.node_styles["expression"])
            
            # 创建节点标签
            label = self._create_node_label(node, show_labels)
            
            # 添加节点属性
            node_attrs = {
                "label": label,
                "shape": style["shape"],
                "style": style["style"],
                "fillcolor": style["fillcolor"],
                "fontname": style["fontname"]
            }
            
            # 添加特殊属性
            if node.properties:
                # 0.4.x特殊标记
                if node.properties.get("is_legacy_constructor"):
                    node_attrs["penwidth"] = "3"
                    node_attrs["color"] = "orange"
                
                if node.properties.get("has_constant_modifier"):
                    node_attrs["peripheries"] = "2"
                
                if node.properties.get("uses_now_keyword"):
                    node_attrs["style"] = style["style"] + ",diagonals"
            
            dot.node(node_id, **node_attrs)
    
    def _add_edges(self, dot: graphviz.Digraph, dfg: DFG, show_labels: bool) -> None:
        """添加边到图中"""
        for edge_id, edge in dfg.edges.items():
            # 获取边样式
            style = self.edge_styles.get(edge.edge_type, self.edge_styles[EdgeType.DATA_DEPENDENCY])
            
            # 创建边标签
            label = self._create_edge_label(edge, show_labels)
            
            # 添加边属性
            edge_attrs = {
                "color": style["color"],
                "style": style["style"],
                "arrowhead": style["arrowhead"]
            }
            
            if label:
                edge_attrs["label"] = label
            
            # 添加权重属性
            if edge.weight > 1:
                edge_attrs["penwidth"] = str(min(edge.weight, 5))
            
            # 添加特殊属性
            if edge.properties:
                if edge.properties.get("relation") == "def-use":
                    edge_attrs["fontcolor"] = "blue"
                elif edge.properties.get("relation") == "state-var-use":
                    edge_attrs["fontcolor"] = "darkgreen"
            
            dot.edge(edge.source_node_id, edge.target_node_id, **edge_attrs)
    
    def _create_node_label(self, node: DFGNode, show_labels: bool) -> str:
        """创建节点标签"""
        if not show_labels:
            return node.node_id
        
        label_parts = []
        
        # 节点类型
        label_parts.append(f"[{node.node_type}]")
        
        # 节点名称
        if node.name:
            label_parts.append(node.name)
        
        # 数据类型
        if node.data_type:
            label_parts.append(f": {node.data_type}")
        
        # 作用域
        if node.scope and node.scope != "global":
            label_parts.append(f"({node.scope})")
        
        return "\\n".join(label_parts)
    
    def _create_edge_label(self, edge: DFGEdge, show_labels: bool) -> str:
        """创建边标签"""
        if not show_labels:
            return ""
        
        label_parts = []
        
        # 边类型
        label_parts.append(edge.edge_type.value)
        
        # 自定义标签
        if edge.label:
            label_parts.append(edge.label)
        
        # 权重
        if edge.weight > 1:
            label_parts.append(f"w:{edge.weight}")
        
        return " ".join(label_parts)
    
    def _create_clustered_graph(self, dfg: DFG, show_labels: bool) -> graphviz.Digraph:
        """创建按作用域聚类的图"""
        dot = graphviz.Digraph(comment=f'Clustered DFG of {dfg.contract_name}',
                             engine=self.engine,
                             format=self.format)
        
        dot.attr(rankdir='TB', splines='ortho', nodesep='0.8', ranksep='1.0')
        
        # 按作用域分组节点
        scopes = {}
        for node_id, node in dfg.nodes.items():
            scope = node.scope or "global"
            if scope not in scopes:
                scopes[scope] = []
            scopes[scope].append(node)
        
        # 暂时禁用聚类功能以避免graphviz API问题
        # 直接添加所有节点到主图
        for node_id, node in dfg.nodes.items():
            style = self.node_styles.get(node.node_type, self.node_styles["expression"])
            label = self._create_node_label(node, show_labels)
            
            dot.node(node_id, 
                    label=label,
                    shape=style["shape"],
                    style=style["style"],
                    fillcolor=style["fillcolor"],
                    fontname=style["fontname"])
        
        # 添加边
        self._add_edges(dot, dfg, show_labels)
        
        return dot
    
    def _create_dfg_from_json(self, data: Dict[str, Any]) -> DFG:
        """从JSON数据创建DFG对象"""
        from .node_types import DFGNode, DFGEdge, EdgeType, ASTNode, SourceLocation
        
        # 创建DFG
        dfg = DFG(
            contract_name=data["contract"],
            solidity_version=data["solidity_version"],
            nodes={},
            edges={},
            metadata=data.get("metadata", {})
        )
        
        # 创建节点
        for node_id, node_data in data["nodes"].items():
            # 创建虚拟AST节点
            from .node_types import NodeType
            ast_node = ASTNode(
                node_id=node_data["id"],
                node_type=NodeType.IDENTIFIER,  # 使用默认类型
                metadata=node_data.get("ast_metadata", {})
            )
            
            if "source_location" in node_data:
                ast_node.source_location = SourceLocation(
                    line=node_data["source_location"]["line"],
                    column=node_data["source_location"]["column"],
                    end_line=node_data["source_location"].get("end_line"),
                    end_column=node_data["source_location"].get("end_column")
                )
            
            ast_node.text = node_data.get("text")
            
            dfg_node = DFGNode(
                node_id=node_data["id"],
                ast_node=ast_node,
                node_type=node_data["type"],
                name=node_data.get("name"),
                data_type=node_data.get("data_type"),
                scope=node_data.get("scope"),
                properties=node_data.get("properties", {})
            )
            
            dfg.nodes[node_id] = dfg_node
        
        # 创建边
        for edge_id, edge_data in data["edges"].items():
            edge_type = EdgeType(edge_data["type"])
            
            dfg_edge = DFGEdge(
                edge_id=edge_data["id"],
                source_node_id=edge_data["source"],
                target_node_id=edge_data["target"],
                edge_type=edge_type,
                label=edge_data.get("label"),
                weight=edge_data.get("weight", 1),
                properties=edge_data.get("properties", {})
            )
            
            dfg.edges[edge_id] = dfg_edge
        
        return dfg
    
    def export_statistics(self, dfg: DFG, output_path: str) -> bool:
        """导出可视化统计信息"""
        try:
            stats = {
                "contract": dfg.contract_name,
                "solidity_version": dfg.solidity_version,
                "visualization_stats": {
                    "total_nodes": len(dfg.nodes),
                    "total_edges": len(dfg.edges),
                    "node_types": {},
                    "edge_types": {},
                    "scopes": set()
                }
            }
            
            # 统计节点类型
            for node in dfg.nodes.values():
                node_type = node.node_type
                stats["visualization_stats"]["node_types"][node_type] = \
                    stats["visualization_stats"]["node_types"].get(node_type, 0) + 1
                
                if node.scope:
                    stats["visualization_stats"]["scopes"].add(node.scope)
            
            # 统计边类型
            for edge in dfg.edges.values():
                edge_type = edge.edge_type.value
                stats["visualization_stats"]["edge_types"][edge_type] = \
                    stats["visualization_stats"]["edge_types"].get(edge_type, 0) + 1
            
            # 转换set为list
            stats["visualization_stats"]["scopes"] = list(stats["visualization_stats"]["scopes"])
            
            # 保存统计信息
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"Error exporting visualization statistics: {e}")
            return False