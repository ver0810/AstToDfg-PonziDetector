#!/usr/bin/env python3
"""
运行所有单元测试的主脚本
"""

import sys
import unittest
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_all_tests():
    """运行所有单元测试"""
    print("=" * 80)
    print(" " * 20 + "🧪 AST-Solidity 单元测试套件")
    print("=" * 80)
    print()
    
    # 创建测试加载器
    loader = unittest.TestLoader()
    
    # 发现并加载所有测试
    test_dir = Path(__file__).parent
    suite = loader.discover(str(test_dir), pattern='test_*.py')
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印总结
    print()
    print("=" * 80)
    print("测试总结:")
    print(f"  运行测试数: {result.testsRun}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print(f"  跳过: {len(result.skipped)}")
    print("=" * 80)
    
    # 返回是否所有测试都通过
    return result.wasSuccessful()


def list_available_tests():
    """列出所有可用的测试"""
    print("=" * 80)
    print("可用的测试模块:")
    print("=" * 80)
    
    test_dir = Path(__file__).parent
    test_files = sorted(test_dir.glob('test_*.py'))
    
    for i, test_file in enumerate(test_files, 1):
        print(f"{i}. {test_file.stem}")
        
        # 尝试导入并列出测试用例
        try:
            module_name = test_file.stem
            module = __import__(module_name)
            
            # 找到所有TestCase类
            test_cases = [
                name for name in dir(module)
                if name.startswith('Test') and hasattr(getattr(module, name), '__bases__')
            ]
            
            if test_cases:
                for test_case in test_cases:
                    print(f"   - {test_case}")
        except Exception as e:
            print(f"   (无法加载: {e})")
    
    print("=" * 80)


def run_specific_test(test_name):
    """运行特定的测试模块"""
    print(f"运行测试: {test_name}")
    print("=" * 80)
    
    loader = unittest.TestLoader()
    
    try:
        # 加载特定测试模块
        suite = loader.loadTestsFromName(test_name)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result.wasSuccessful()
    except Exception as e:
        print(f"错误: 无法加载测试 {test_name}")
        print(f"详情: {e}")
        return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='AST-Solidity 单元测试运行器')
    parser.add_argument('--list', '-l', action='store_true', help='列出所有可用的测试')
    parser.add_argument('--test', '-t', type=str, help='运行特定的测试模块')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    if args.list:
        list_available_tests()
    elif args.test:
        success = run_specific_test(args.test)
        sys.exit(0 if success else 1)
    else:
        success = run_all_tests()
        sys.exit(0 if success else 1)
