#!/usr/bin/env python3
"""
验证DFG配置模块
测试配置功能是否正常工作
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_config():
    """测试配置模块"""
    print("🧪 测试DFG配置模块")
    print("=" * 70)
    
    try:
        from src.dfg_builder.dfg_config import (
            DFGConfig, OutputMode, NodePriority, EdgePriority,
            get_node_priority, should_keep_node,
            CRITICAL_NODE_TYPES, IMPORTANT_NODE_TYPES, KEYWORD_PATTERNS
        )
        print("✅ 成功导入dfg_config模块\n")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False
    
    # 测试1: 创建不同模式的配置
    print("测试1: 创建不同模式的配置")
    print("-" * 70)
    
    configs = {
        "精简模式": DFGConfig.compact(),
        "标准模式": DFGConfig.standard(),
        "详细模式": DFGConfig.verbose()
    }
    
    for name, config in configs.items():
        print(f"\n{name}:")
        print(f"  输出模式: {config.output_mode.value}")
        print(f"  跳过关键字: {config.skip_keywords}")
        print(f"  跳过类型名: {config.skip_type_names}")
        print(f"  合并简单表达式: {config.merge_simple_expressions}")
        print(f"  包含节点文本: {config.include_node_text}")
        print(f"  最小节点优先级: {config.min_node_priority.value}")
    
    # 测试2: 节点优先级判断
    print("\n\n测试2: 节点优先级判断")
    print("-" * 70)
    
    test_nodes = [
        ("contract", None, "MyContract"),
        ("function", None, "transfer"),
        ("state_variable", "balance", "uint256"),
        ("identifier", None, "pragma"),
        ("identifier", None, "uint"),
        ("identifier", None, "+"),
        ("number_literal", None, "42"),
    ]
    
    for node_type, node_name, node_text in test_nodes:
        priority = get_node_priority(node_type, node_name, node_text)
        print(f"  {node_type:20} | {str(node_text):15} | 优先级: {priority.value}")
    
    # 测试3: 节点过滤判断
    print("\n\n测试3: 节点过滤判断（标准模式）")
    print("-" * 70)
    
    standard_config = DFGConfig.standard()
    
    for node_type, node_name, node_text in test_nodes:
        should_keep = should_keep_node(node_type, node_name or "", node_text or "", standard_config)
        status = "✅ 保留" if should_keep else "❌ 过滤"
        print(f"  {status} | {node_type:20} | {str(node_text):15}")
    
    # 测试4: 自定义配置
    print("\n\n测试4: 自定义配置")
    print("-" * 70)
    
    custom_config = DFGConfig(
        output_mode=OutputMode.CUSTOM,
        skip_keywords=False,  # 不跳过关键字
        skip_literal_nodes=True,  # 跳过字面量
        include_node_text=True,
        text_max_length=100
    )
    
    print(f"自定义配置:")
    print(f"  跳过关键字: {custom_config.skip_keywords}")
    print(f"  跳过字面量: {custom_config.skip_literal_nodes}")
    print(f"  包含文本: {custom_config.include_node_text}")
    print(f"  文本长度限制: {custom_config.text_max_length}")
    
    print("\n使用自定义配置的过滤结果:")
    for node_type, node_name, node_text in test_nodes:
        should_keep = should_keep_node(node_type, node_name or "", node_text or "", custom_config)
        status = "✅ 保留" if should_keep else "❌ 过滤"
        print(f"  {status} | {node_type:20} | {str(node_text):15}")
    
    # 测试5: 统计关键节点类型
    print("\n\n测试5: 节点分类统计")
    print("-" * 70)
    
    print(f"核心节点类型数量: {len(CRITICAL_NODE_TYPES)}")
    print(f"  {', '.join(sorted(CRITICAL_NODE_TYPES))}")
    
    print(f"\n重要节点类型数量: {len(IMPORTANT_NODE_TYPES)}")
    print(f"  {', '.join(sorted(list(IMPORTANT_NODE_TYPES)[:5]))}...")
    
    print(f"\n关键字模式数量: {len(KEYWORD_PATTERNS)}")
    print(f"  {', '.join(sorted(list(KEYWORD_PATTERNS)[:10]))}...")
    
    print("\n\n✅ 所有配置测试通过!")
    return True

if __name__ == "__main__":
    success = test_config()
    sys.exit(0 if success else 1)
