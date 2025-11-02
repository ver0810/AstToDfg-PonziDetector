#!/usr/bin/env python3
"""
展示DFG节点粒度优化功能的示例脚本
演示如何使用不同的配置模式
"""

import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    print("🚀 Solidity AST to DFG - 节点粒度优化示例")
    print("=" * 70)
    
    try:
        from src.analyzer import SolidityAnalyzer
        from src.dfg_config import DFGConfig, OutputMode
        print("✅ 成功导入分析器和配置")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("请确保已安装所有依赖:")
        print("  pip install -r requirements.txt")
        return 1
    
    # 示例: 使用标准模式（推荐）
    print("\n" + "="*70)
    print("  示例 1: 使用标准模式（推荐配置）")
    print("="*70)
    
    print("\n创建标准模式配置...")
    config = DFGConfig.standard()
    
    print(f"配置详情:")
    print(f"  - 输出模式: {config.output_mode.value}")
    print(f"  - 跳过关键字: {config.skip_keywords}")
    print(f"  - 跳过类型名: {config.skip_type_names}")
    print(f"  - 合并简单表达式: {config.merge_simple_expressions}")
    print(f"  - 包含节点文本: {config.include_node_text}")
    print(f"  - 文本最大长度: {config.text_max_length}")
    
    # 创建分析器
    analyzer = SolidityAnalyzer(
        solidity_version="0.4.x",
        dfg_config=config
    )
    
    # 分析示例合约
    example_contract = """
pragma solidity 0.4.24;

contract SimpleStorage {
    uint256 public storedData;
    
    function SimpleStorage(uint256 initialValue) public {
        storedData = initialValue;
    }
    
    function set(uint256 data) public {
        storedData = data;
    }
    
    function get() public constant returns (uint256) {
        return storedData;
    }
}
"""
    
    print("\n分析合约...")
    result = analyzer.analyze_source(example_contract, "SimpleStorage")
    
    if result['success']:
        print(f"\n✅ 分析成功!")
        print(f"   合约: {result['contract']}")
        print(f"   AST节点: {result['ast_nodes']}")
        print(f"   DFG节点: {result['dfg_nodes']} (过滤了 {result['filtered_nodes']} 个)")
        print(f"   DFG边: {result['dfg_edges']} (过滤了 {result['filtered_edges']} 个)")
        print(f"   节点减少率: {result['optimization_stats']['reduction_rate']}")
        if 'json_file' in result:
            print(f"   JSON文件: {result['json_file']}")
    else:
        print(f"❌ 分析失败: {result['error']}")
    
    # 示例: 精简模式
    print("\n" + "="*70)
    print("  示例 2: 使用精简模式（最小化输出）")
    print("="*70)
    
    config_compact = DFGConfig.compact()
    analyzer_compact = SolidityAnalyzer(
        solidity_version="0.4.x",
        output_dir="output/compact",
        dfg_config=config_compact
    )
    
    result_compact = analyzer_compact.analyze_source(example_contract, "SimpleStorage_Compact")
    
    if result_compact['success']:
        print(f"\n✅ 精简模式分析成功!")
        print(f"   DFG节点: {result_compact['dfg_nodes']}")
        print(f"   节点减少率: {result_compact['optimization_stats']['reduction_rate']}")
    
    # 示例: 自定义配置
    print("\n" + "="*70)
    print("  示例 3: 自定义配置")
    print("="*70)
    
    custom_config = DFGConfig(
        output_mode=OutputMode.CUSTOM,
        skip_keywords=True,
        skip_type_names=True,
        skip_literal_nodes=False,  # 保留字面量
        include_node_text=True,     # 包含文本
        text_max_length=50,         # 限制文本长度
        store_source_location=True
    )
    
    print(f"自定义配置:")
    print(f"  - 保留字面量节点")
    print(f"  - 包含节点文本（最大50字符）")
    print(f"  - 存储源码位置")
    
    analyzer_custom = SolidityAnalyzer(
        solidity_version="0.4.x",
        output_dir="output/custom",
        dfg_config=custom_config
    )
    
    result_custom = analyzer_custom.analyze_source(example_contract, "SimpleStorage_Custom")
    
    if result_custom['success']:
        print(f"\n✅ 自定义配置分析成功!")
        print(f"   DFG节点: {result_custom['dfg_nodes']}")
    
    # 示例: 分析真实合约文件
    print("\n" + "="*70)
    print("  示例 4: 分析真实合约文件")
    print("="*70)
    
    dfs_file = Path("examples/solidity_04x/DFS.sol")
    if dfs_file.exists():
        print(f"\n分析文件: {dfs_file}")
        
        # 使用标准配置
        result_dfs = analyzer.analyze_file(str(dfs_file))
        
        if result_dfs['success']:
            print(f"\n✅ DFS合约分析结果:")
            print(f"   合约: {result_dfs['contract']}")
            print(f"   AST节点: {result_dfs['ast_nodes']}")
            print(f"   DFG节点: {result_dfs['dfg_nodes']}")
            print(f"   过滤节点: {result_dfs['filtered_nodes']}")
            print(f"   节点减少率: {result_dfs['optimization_stats']['reduction_rate']}")
            
            # 计算文件大小
            if 'json_file' in result_dfs:
                json_path = Path(result_dfs['json_file'])
                if json_path.exists():
                    size_kb = json_path.stat().st_size / 1024
                    print(f"   输出文件大小: {size_kb:.2f} KB")
    else:
        print(f"⚠️  示例文件不存在: {dfs_file}")
    
    # 总结
    print("\n" + "="*70)
    print("  💡 使用建议")
    print("="*70)
    print("""
1. 标准模式（推荐）:
   config = DFGConfig.standard()
   - 平衡的节点过滤
   - 合理的文件大小
   - 适合大多数场景

2. 精简模式（快速分析）:
   config = DFGConfig.compact()
   - 最小化节点数
   - 最小文件大小
   - 适合大规模批量分析

3. 详细模式（完整信息）:
   config = DFGConfig.verbose()
   - 保留所有节点
   - 完整的AST信息
   - 适合深度分析和调试

4. 自定义模式（灵活配置）:
   config = DFGConfig(output_mode=OutputMode.CUSTOM, ...)
   - 根据需求自定义
   - 精确控制输出内容
    """)
    
    print("\n✅ 示例演示完成!")
    print(f"\n📁 查看输出文件: output/dfgs/")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
