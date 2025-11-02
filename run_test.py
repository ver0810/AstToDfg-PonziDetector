#!/usr/bin/env python3
"""
完整测试：验证DFG节点粒度优化的实际效果
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_optimization():
    """测试优化效果"""
    print("🚀 DFG节点粒度优化 - 完整测试")
    print("=" * 70)
    
    # 导入模块
    try:
        from src.analyzer import SolidityAnalyzer
        from src.dfg_config import DFGConfig, OutputMode
        print("✅ 模块导入成功\n")
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 测试合约
    
    with open('examples/solidity_04x/DFS.sol', 'r', encoding='utf-8') as file:
      test_contract = file.read()
    
    print("\n" + "=" * 70)
    print("  测试 2: 标准模式（推荐配置）")
    print("=" * 70)
    
    try:
        config_standard = DFGConfig.sta()
        analyzer_standard = SolidityAnalyzer(
            solidity_version="0.4.x",
            output_dir="output/verbose",
            dfg_config=config_standard
        )
        
        result_standard = analyzer_standard.analyze_source(test_contract, "SimpleStorage_Standard")
        
        if result_standard.get('success'):
            print(f"✅ 标准模式分析成功")
            print(f"   DFG节点: {result_standard['dfg_nodes']}")
            print(f"   DFG边: {result_standard['dfg_edges']}")
            print(f"   过滤节点: {result_standard.get('filtered_nodes', 0)}")
            print(f"   过滤边: {result_standard.get('filtered_edges', 0)}")
            
        else:
            print(f"❌ 分析失败: {result_standard.get('error')}")
            
    except Exception as e:
        print(f"❌ 标准模式测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    success = test_optimization()
    sys.exit(0 if success else 1)
