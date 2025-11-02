#!/usr/bin/env python3
"""
DFG配置模块单元测试
测试DFG节点过滤和优化配置
"""

import sys
import unittest
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.dfg_builder.dfg_config import (
    DFGConfig,
    OutputMode,
    NodePriority,
    EdgePriority,
    get_node_priority,
    should_keep_node,
    CRITICAL_NODE_TYPES,
    IMPORTANT_NODE_TYPES,
    AUXILIARY_NODE_TYPES,
    KEYWORD_PATTERNS
)


class TestOutputMode(unittest.TestCase):
    """OutputMode 枚举测试"""
    
    def test_output_modes(self):
        """测试输出模式值"""
        self.assertEqual(OutputMode.COMPACT.value, "compact")
        self.assertEqual(OutputMode.STANDARD.value, "standard")
        self.assertEqual(OutputMode.VERBOSE.value, "verbose")
        self.assertEqual(OutputMode.CUSTOM.value, "custom")


class TestNodePriority(unittest.TestCase):
    """NodePriority 枚举测试"""
    
    def test_priority_values(self):
        """测试优先级值"""
        self.assertEqual(NodePriority.CRITICAL.value, "critical")
        self.assertEqual(NodePriority.IMPORTANT.value, "important")
        self.assertEqual(NodePriority.AUXILIARY.value, "auxiliary")
        self.assertEqual(NodePriority.DISCARD.value, "discard")


class TestDFGConfig(unittest.TestCase):
    """DFGConfig 类测试"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = DFGConfig()
        self.assertEqual(config.output_mode, OutputMode.STANDARD)
        self.assertTrue(config.skip_keywords)
        self.assertTrue(config.skip_type_names)
        self.assertFalse(config.skip_literal_nodes)
        self.assertEqual(config.min_node_priority, NodePriority.IMPORTANT)
    
    def test_compact_config(self):
        """测试紧凑模式配置"""
        config = DFGConfig.compact()
        self.assertEqual(config.output_mode, OutputMode.COMPACT)
        self.assertTrue(config.skip_keywords)
        self.assertTrue(config.skip_type_names)
        self.assertTrue(config.skip_operators)
        self.assertTrue(config.skip_punctuation)
        self.assertTrue(config.skip_literal_nodes)
        self.assertFalse(config.include_node_text)
        self.assertEqual(config.min_node_priority, NodePriority.CRITICAL)
    
    def test_standard_config(self):
        """测试标准模式配置"""
        config = DFGConfig.standard()
        self.assertEqual(config.output_mode, OutputMode.STANDARD)
        self.assertTrue(config.skip_keywords)
        self.assertTrue(config.skip_type_names)
        self.assertFalse(config.skip_literal_nodes)
        self.assertFalse(config.include_node_text)
        self.assertEqual(config.min_node_priority, NodePriority.IMPORTANT)
    
    def test_verbose_config(self):
        """测试详细模式配置"""
        config = DFGConfig.verbose()
        self.assertEqual(config.output_mode, OutputMode.VERBOSE)
        self.assertFalse(config.skip_keywords)
        self.assertFalse(config.skip_type_names)
        self.assertFalse(config.skip_literal_nodes)
        self.assertTrue(config.include_node_text)
        self.assertTrue(config.include_ast_metadata)
        self.assertEqual(config.min_node_priority, NodePriority.AUXILIARY)
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = DFGConfig(
            output_mode=OutputMode.CUSTOM,
            skip_keywords=False,
            include_node_text=True,
            text_max_length=100,
            min_node_priority=NodePriority.CRITICAL
        )
        self.assertEqual(config.output_mode, OutputMode.CUSTOM)
        self.assertFalse(config.skip_keywords)
        self.assertTrue(config.include_node_text)
        self.assertEqual(config.text_max_length, 100)
        self.assertEqual(config.min_node_priority, NodePriority.CRITICAL)


class TestNodePriorityFunction(unittest.TestCase):
    """节点优先级判断函数测试"""
    
    def test_critical_nodes(self):
        """测试关键节点识别"""
        for node_type in CRITICAL_NODE_TYPES:
            priority = get_node_priority(node_type, node_type)
            self.assertEqual(priority, NodePriority.CRITICAL,
                           f"{node_type} should be CRITICAL")
    
    def test_important_nodes(self):
        """测试重要节点识别"""
        for node_type in IMPORTANT_NODE_TYPES:
            priority = get_node_priority(node_type, node_type)
            self.assertEqual(priority, NodePriority.IMPORTANT,
                           f"{node_type} should be IMPORTANT")
    
    def test_auxiliary_nodes(self):
        """测试辅助节点识别"""
        for node_type in AUXILIARY_NODE_TYPES:
            priority = get_node_priority(node_type, node_type)
            self.assertEqual(priority, NodePriority.AUXILIARY,
                           f"{node_type} should be AUXILIARY")
    
    def test_keyword_nodes(self):
        """测试关键字节点识别"""
        keywords = ["public", "private", "function", "contract", "uint", "address"]
        for keyword in keywords:
            priority = get_node_priority("identifier", keyword)
            self.assertEqual(priority, NodePriority.DISCARD,
                           f"{keyword} should be DISCARD")
    
    def test_variable_identifier(self):
        """测试变量标识符识别"""
        priority = get_node_priority("identifier", "myVariable")
        self.assertEqual(priority, NodePriority.IMPORTANT)
    
    def test_unknown_node_type(self):
        """测试未知节点类型"""
        priority = get_node_priority("unknown_type", "test")
        self.assertEqual(priority, NodePriority.AUXILIARY)


class TestShouldKeepNode(unittest.TestCase):
    """节点保留判断函数测试"""
    
    def test_keep_critical_in_compact_mode(self):
        """测试紧凑模式保留关键节点"""
        config = DFGConfig.compact()
        self.assertTrue(should_keep_node("contract", "MyContract", "MyContract", config))
        self.assertTrue(should_keep_node("function", "myFunction", "myFunction", config))
    
    def test_discard_important_in_compact_mode(self):
        """测试紧凑模式丢弃重要节点"""
        config = DFGConfig.compact()
        self.assertFalse(should_keep_node("identifier", "myVariable", "myVariable", config))
    
    def test_keep_important_in_standard_mode(self):
        """测试标准模式保留重要节点"""
        config = DFGConfig.standard()
        self.assertTrue(should_keep_node("identifier", "myVariable", "myVariable", config))
        self.assertTrue(should_keep_node("local_variable", "x", "x", config))
    
    def test_discard_keywords_in_standard_mode(self):
        """测试标准模式丢弃关键字"""
        config = DFGConfig.standard()
        self.assertFalse(should_keep_node("identifier", "public", "public", config))
        self.assertFalse(should_keep_node("identifier", "uint", "uint", config))
    
    def test_keep_all_in_verbose_mode(self):
        """测试详细模式保留所有节点"""
        config = DFGConfig.verbose()
        self.assertTrue(should_keep_node("identifier", "public", "public", config))
        self.assertTrue(should_keep_node("identifier", "myVariable", "myVariable", config))
        self.assertTrue(should_keep_node("contract", "MyContract", "MyContract", config))
    
    def test_skip_keywords_option(self):
        """测试跳过关键字选项"""
        config = DFGConfig(skip_keywords=True, min_node_priority=NodePriority.AUXILIARY)
        self.assertFalse(should_keep_node("identifier", "function", "function", config))
        
        config = DFGConfig(skip_keywords=False, min_node_priority=NodePriority.AUXILIARY)
        self.assertTrue(should_keep_node("identifier", "function", "function", config))
    
    def test_skip_literal_nodes_option(self):
        """测试跳过字面量节点选项"""
        config = DFGConfig(skip_literal_nodes=True, min_node_priority=NodePriority.AUXILIARY)
        self.assertFalse(should_keep_node("number_literal", "42", "42", config))
        
        config = DFGConfig(skip_literal_nodes=False, min_node_priority=NodePriority.AUXILIARY)
        self.assertTrue(should_keep_node("number_literal", "42", "42", config))


class TestEdgeConfiguration(unittest.TestCase):
    """边配置测试"""
    
    def test_edge_filtering_options(self):
        """测试边过滤选项"""
        config = DFGConfig.compact()
        self.assertTrue(config.skip_sequential_control)
        self.assertTrue(config.skip_redundant_edges)
        self.assertTrue(config.merge_parallel_edges)
    
    def test_edge_priority_levels(self):
        """测试边优先级级别"""
        self.assertEqual(EdgePriority.HIGH.value, "high")
        self.assertEqual(EdgePriority.MEDIUM.value, "medium")
        self.assertEqual(EdgePriority.LOW.value, "low")
    
    def test_edge_filtering_in_standard_mode(self):
        """测试标准模式的边过滤"""
        config = DFGConfig.standard()
        self.assertTrue(config.skip_sequential_control)
        self.assertTrue(config.skip_redundant_edges)
        self.assertEqual(config.min_edge_priority, EdgePriority.MEDIUM)
    
    def test_edge_filtering_in_verbose_mode(self):
        """测试详细模式的边过滤"""
        config = DFGConfig.verbose()
        self.assertFalse(config.skip_sequential_control)
        self.assertFalse(config.skip_redundant_edges)


class TestKeywordPatterns(unittest.TestCase):
    """关键字模式测试"""
    
    def test_keyword_patterns_exist(self):
        """测试关键字模式列表存在"""
        self.assertIsInstance(KEYWORD_PATTERNS, (list, tuple, set))
        self.assertGreater(len(KEYWORD_PATTERNS), 0)
    
    def test_common_keywords_in_patterns(self):
        """测试常见关键字在模式中"""
        common_keywords = ["public", "private", "function", "contract", "uint", "address"]
        for keyword in common_keywords:
            self.assertIn(keyword, KEYWORD_PATTERNS,
                         f"{keyword} should be in KEYWORD_PATTERNS")
    
    def test_solidity_types_in_patterns(self):
        """测试Solidity类型在模式中"""
        types = ["uint", "uint256", "address", "bool", "string", "bytes"]
        for type_name in types:
            found = any(type_name in pattern for pattern in KEYWORD_PATTERNS)
            self.assertTrue(found, f"{type_name} should be in KEYWORD_PATTERNS")


class TestNodeTypeCategories(unittest.TestCase):
    """节点类型分类测试"""
    
    def test_critical_types_defined(self):
        """测试关键节点类型已定义"""
        self.assertIsInstance(CRITICAL_NODE_TYPES, (list, tuple, set))
        self.assertGreater(len(CRITICAL_NODE_TYPES), 0)
        self.assertIn("contract", CRITICAL_NODE_TYPES)
        self.assertIn("function", CRITICAL_NODE_TYPES)
    
    def test_important_types_defined(self):
        """测试重要节点类型已定义"""
        self.assertIsInstance(IMPORTANT_NODE_TYPES, (list, tuple, set))
        self.assertGreater(len(IMPORTANT_NODE_TYPES), 0)
    
    def test_auxiliary_types_defined(self):
        """测试辅助节点类型已定义"""
        self.assertIsInstance(AUXILIARY_NODE_TYPES, (list, tuple, set))
        self.assertGreater(len(AUXILIARY_NODE_TYPES), 0)
    
    def test_no_overlap_in_categories(self):
        """测试分类之间没有重叠"""
        critical_set = set(CRITICAL_NODE_TYPES)
        important_set = set(IMPORTANT_NODE_TYPES)
        auxiliary_set = set(AUXILIARY_NODE_TYPES)
        
        self.assertEqual(len(critical_set & important_set), 0,
                        "Critical and Important should not overlap")
        self.assertEqual(len(critical_set & auxiliary_set), 0,
                        "Critical and Auxiliary should not overlap")
        self.assertEqual(len(important_set & auxiliary_set), 0,
                        "Important and Auxiliary should not overlap")


if __name__ == '__main__':
    print("🧪 测试 DFG 配置模块")
    print("=" * 70)
    unittest.main(verbosity=2)
