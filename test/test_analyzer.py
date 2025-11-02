#!/usr/bin/env python3
"""
测试脚本
用于测试Solidity AST到DFG的构建功能
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试基本功能 ===")
    
    try:
        from src.analyzer import SolidityAnalyzer
        
        # 创建分析器
        analyzer = SolidityAnalyzer(solidity_version="0.4.x")
        
        # 验证设置
        validation = analyzer.validate_setup()
        print("验证结果:")
        for key, value in validation.items():
            print(f"  {key}: {value}")
        
        if not validation.get("components_ready", False):
            print("❌ 组件未正确初始化")
            return False
        
        print("✅ 基本功能测试通过")
        return True
        
    except Exception as e:
        print(f"❌ 基本功能测试失败: {e}")
        return False

def test_simple_contract():
    """测试简单合约分析"""
    print("\n=== 测试简单合约分析 ===")
    
    try:
        from src.analyzer import SolidityAnalyzer
        
        analyzer = SolidityAnalyzer(solidity_version="0.4.x")
        
        # 测试简单合约
        simple_contract = """
        pragma solidity 0.4.24;
        
        contract Test {
            uint256 public value;
            
            function Test() public {
                value = 0;
            }
            
            function setValue(uint256 _value) public {
                value = _value;
            }
            
            function getValue() public constant returns (uint256) {
                return value;
            }
        }
        """
        
        result = analyzer.analyze_source(simple_contract, "TestContract")
        
        print("分析结果:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        
        if result.get("success", False):
            print("✅ 简单合约分析测试通过")
            return True
        else:
            print(f"❌ 简单合约分析测试失败: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 简单合约分析测试失败: {e}")
        return False

def test_file_analysis():
    """测试文件分析"""
    print("\n=== 测试文件分析 ===")
    
    try:
        from src.analyzer import SolidityAnalyzer
        
        analyzer = SolidityAnalyzer(solidity_version="0.4.x")
        
        # 测试文件路径
        test_file = "examples/solidity_04x/DFS.sol"
        
        if not Path(test_file).exists():
            print(f"❌ 测试文件不存在: {test_file}")
            return False
        
        result = analyzer.analyze_file(test_file)
        
        print("文件分析结果:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        
        if result.get("success", False):
            print("✅ 文件分析测试通过")
            return True
        else:
            print(f"❌ 文件分析测试失败: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ 文件分析测试失败: {e}")
        return False

def test_directory_analysis():
    """测试目录分析"""
    print("\n=== 测试目录分析 ===")
    
    try:
        from src.analyzer import SolidityAnalyzer
        
        analyzer = SolidityAnalyzer(solidity_version="0.4.x")
        
        # 测试目录路径
        test_dir = "examples/solidity_04x"
        
        if not Path(test_dir).exists():
            print(f"❌ 测试目录不存在: {test_dir}")
            return False
        
        result = analyzer.analyze_directory(test_dir)
        
        print("目录分析结果:")
        print(f"  总文件数: {result.get('total_files', 0)}")
        print(f"  成功分析: {result.get('successful_analyses', 0)}")
        print(f"  失败分析: {result.get('failed_analyses', 0)}")
        
        if result.get("total_files", 0) > 0:
            print("✅ 目录分析测试通过")
            return True
        else:
            print("❌ 目录分析测试失败: 没有找到文件")
            return False
            
    except Exception as e:
        print(f"❌ 目录分析测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试Solidity AST到DFG构建系统")
    print("=" * 50)
    
    tests = [
        # test_basic_functionality,
        # test_simple_contract,
        test_file_analysis,
        # test_directory_analysis
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
        return 0
    else:
        print("⚠️  部分测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())