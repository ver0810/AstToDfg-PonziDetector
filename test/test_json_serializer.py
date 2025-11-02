#!/usr/bin/env python3
"""
JSON序列化器单元测试
测试DFG序列化功能
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.json_serializer import JSONSerializer
from src.dfg_builder.dfg_config import DFGConfig, OutputMode


class TestJSONSerializer(unittest.TestCase):
    """JSON序列化器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.config = DFGConfig.standard()
        self.serializer = JSONSerializer(config=self.config)
    
    def test_initialization(self):
        """测试序列化器初始化"""
        serializer = JSONSerializer()
        self.assertIsNotNone(serializer.config)
        self.assertEqual(serializer.indent, 2)
        
        serializer = JSONSerializer(indent=4)
        self.assertEqual(serializer.indent, 4)
    
    def test_initialization_with_config(self):
        """测试使用配置初始化"""
        config = DFGConfig.compact()
        serializer = JSONSerializer(config=config)
        self.assertEqual(serializer.config.output_mode, OutputMode.COMPACT)
    
    def test_serialize_empty_dfg(self):
        """测试序列化空DFG"""
        result = self.serializer.serialize_dfg(None)
        self.assertEqual(result, {})
    
    def test_serialize_dfg_structure(self):
        """测试DFG序列化结构"""
        # 创建模拟DFG对象
        mock_dfg = Mock()
        mock_dfg.contract_name = "TestContract"
        mock_dfg.solidity_version = "0.4.25"
        mock_dfg.nodes = {}
        mock_dfg.edges = {}
        mock_dfg.entry_node_id = "node_0"
        
        result = self.serializer.serialize_dfg(mock_dfg)
        
        self.assertIn("contract", result)
        self.assertIn("solidity_version", result)
        self.assertIn("nodes", result)
        self.assertIn("edges", result)
        self.assertIn("metadata", result)
        self.assertIn("entry_node_id", result)
        
        self.assertEqual(result["contract"], "TestContract")
        self.assertEqual(result["solidity_version"], "0.4.25")
        self.assertEqual(result["entry_node_id"], "node_0")
    
    def test_serialize_node_basic_fields(self):
        """测试节点序列化基本字段"""
        # 创建模拟节点
        mock_ast_node = Mock()
        mock_ast_node.text = "myFunction"
        mock_ast_node.source_location = None
        
        mock_node = Mock()
        mock_node.node_id = "node_1"
        mock_node.node_type = "function"
        mock_node.name = "myFunction"
        mock_node.data_type = "function"
        mock_node.scope = "contract"
        mock_node.ast_node = mock_ast_node
        mock_node.properties = {"visibility": "public"}
        
        mock_dfg = Mock()
        mock_dfg.contract_name = "Test"
        mock_dfg.solidity_version = "0.4.25"
        mock_dfg.nodes = {"node_1": mock_node}
        mock_dfg.edges = {}
        mock_dfg.entry_node_id = None
        
        result = self.serializer.serialize_dfg(mock_dfg)
        
        self.assertIn("nodes", result)
        nodes = result["nodes"]
        self.assertIn("node_1", nodes)
        
        node = nodes["node_1"]
        self.assertEqual(node["id"], "node_1")
        self.assertEqual(node["type"], "function")
        self.assertEqual(node["name"], "myFunction")
        self.assertIn("properties", node)
    
    def test_node_text_inclusion_based_on_config(self):
        """测试基于配置包含节点文本"""
        # 配置包含文本
        config_with_text = DFGConfig(include_node_text=True)
        serializer = JSONSerializer(config=config_with_text)
        
        mock_ast_node = Mock()
        mock_ast_node.text = "test text"
        
        mock_node = Mock()
        mock_node.node_id = "node_1"
        mock_node.node_type = "identifier"
        mock_node.name = "test"
        mock_node.data_type = None
        mock_node.scope = None
        mock_node.ast_node = mock_ast_node
        mock_node.properties = {}
        
        mock_dfg = Mock()
        mock_dfg.contract_name = "Test"
        mock_dfg.solidity_version = "0.4.25"
        mock_dfg.nodes = {"node_1": mock_node}
        mock_dfg.edges = {}
        mock_dfg.entry_node_id = None
        
        result = serializer.serialize_dfg(mock_dfg)
        self.assertIn("text", result["nodes"]["node_1"])
        self.assertEqual(result["nodes"]["node_1"]["text"], "test text")
    
    def test_node_text_truncation(self):
        """测试节点文本截断"""
        config = DFGConfig(include_node_text=True, text_max_length=10)
        serializer = JSONSerializer(config=config)
        
        mock_ast_node = Mock()
        mock_ast_node.text = "this is a very long text that should be truncated"
        
        mock_node = Mock()
        mock_node.node_id = "node_1"
        mock_node.node_type = "identifier"
        mock_node.name = "test"
        mock_node.data_type = None
        mock_node.scope = None
        mock_node.ast_node = mock_ast_node
        mock_node.properties = {}
        
        mock_dfg = Mock()
        mock_dfg.contract_name = "Test"
        mock_dfg.solidity_version = "0.4.25"
        mock_dfg.nodes = {"node_1": mock_node}
        mock_dfg.edges = {}
        mock_dfg.entry_node_id = None
        
        result = serializer.serialize_dfg(mock_dfg)
        text = result["nodes"]["node_1"]["text"]
        self.assertTrue(len(text) <= 13)  # 10 + "..."
        self.assertTrue(text.endswith("..."))
    
    def test_serialize_edge(self):
        """测试边序列化"""
        from src.ast_builder.node_types import EdgeType
        
        mock_edge = Mock()
        mock_edge.edge_id = "edge_1"
        mock_edge.source_node_id = "node_1"
        mock_edge.target_node_id = "node_2"
        mock_edge.edge_type = EdgeType.CONTROL_FLOW
        mock_edge.label = "if_true"
        mock_edge.weight = 1.0
        mock_edge.properties = {"condition": "x > 0"}
        
        mock_dfg = Mock()
        mock_dfg.contract_name = "Test"
        mock_dfg.solidity_version = "0.4.25"
        mock_dfg.nodes = {}
        mock_dfg.edges = {"edge_1": mock_edge}
        mock_dfg.entry_node_id = None
        
        result = self.serializer.serialize_dfg(mock_dfg)
        
        self.assertIn("edges", result)
        edges = result["edges"]
        self.assertIn("edge_1", edges)
        
        edge = edges["edge_1"]
        self.assertEqual(edge["id"], "edge_1")
        self.assertEqual(edge["source"], "node_1")
        self.assertEqual(edge["target"], "node_2")
        self.assertEqual(edge["label"], "if_true")
        self.assertIn("properties", edge)


class TestJSONSerializerIntegration(unittest.TestCase):
    """JSON序列化器集成测试"""
    
    def test_different_output_modes(self):
        """测试不同输出模式"""
        modes = [
            (OutputMode.COMPACT, False),
            (OutputMode.STANDARD, False),
            (OutputMode.VERBOSE, True)
        ]
        
        for mode, include_text in modes:
            config = DFGConfig(output_mode=mode)
            serializer = JSONSerializer(config=config)
            
            self.assertEqual(serializer.config.output_mode, mode)
            self.assertEqual(serializer.config.include_node_text, include_text)
    
    def test_serializer_indentation(self):
        """测试序列化缩进"""
        for indent in [2, 4, None]:
            serializer = JSONSerializer(indent=indent)
            self.assertEqual(serializer.indent, indent)


if __name__ == '__main__':
    print("🧪 测试 JSON 序列化器")
    print("=" * 70)
    unittest.main(verbosity=2)
