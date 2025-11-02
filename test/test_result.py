#!/usr/bin/env python3
"""
Result 类型单元测试
测试函数式错误处理功能
"""

import sys
import unittest
from pathlib import Path

# 添加src目录到Python路径  
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 只导入需要的模块，不触发完整的src导入
sys.path.insert(0, str(project_root / "src" / "utils"))
from result import Result


class TestResult(unittest.TestCase):
    """Result 类型测试"""
    
    def test_success_creation(self):
        """测试创建成功结果"""
        result = Result.success(42)
        self.assertTrue(result.is_success)
        self.assertFalse(result.is_failure)
        self.assertEqual(result.value, 42)
    
    def test_failure_creation(self):
        """测试创建失败结果"""
        result = Result.failure("Error occurred")
        self.assertTrue(result.is_failure)
        self.assertFalse(result.is_success)
        self.assertEqual(result.error, "Error occurred")
    
    def test_value_access_on_failure_raises(self):
        """测试访问失败结果的值会抛出异常"""
        result = Result.failure("Error")
        with self.assertRaises(ValueError):
            _ = result.value
    
    def test_error_access_on_success_raises(self):
        """测试访问成功结果的错误会抛出异常"""
        result = Result.success(42)
        with self.assertRaises(ValueError):
            _ = result.error
    
    def test_map_on_success(self):
        """测试在成功结果上映射"""
        result = Result.success(10)
        mapped = result.map(lambda x: x * 2)
        self.assertTrue(mapped.is_success)
        self.assertEqual(mapped.value, 20)
    
    def test_map_on_failure(self):
        """测试在失败结果上映射"""
        result = Result.failure("Error")
        mapped = result.map(lambda x: x * 2)
        self.assertTrue(mapped.is_failure)
        self.assertEqual(mapped.error, "Error")
    
    def test_map_exception_handling(self):
        """测试映射函数抛出异常的处理"""
        result = Result.success(10)
        mapped = result.map(lambda x: 1 / 0)
        self.assertTrue(mapped.is_failure)
        self.assertIn("division", mapped.error.lower())
    
    def test_flat_map_on_success(self):
        """测试在成功结果上平面映射"""
        result = Result.success(10)
        flat_mapped = result.flat_map(lambda x: Result.success(x * 2))
        self.assertTrue(flat_mapped.is_success)
        self.assertEqual(flat_mapped.value, 20)
    
    def test_flat_map_on_failure(self):
        """测试在失败结果上平面映射"""
        result = Result.failure("Error")
        flat_mapped = result.flat_map(lambda x: Result.success(x * 2))
        self.assertTrue(flat_mapped.is_failure)
        self.assertEqual(flat_mapped.error, "Error")
    
    def test_flat_map_returns_failure(self):
        """测试平面映射返回失败结果"""
        result = Result.success(10)
        flat_mapped = result.flat_map(lambda x: Result.failure("Custom error"))
        self.assertTrue(flat_mapped.is_failure)
        self.assertEqual(flat_mapped.error, "Custom error")
    
    def test_unwrap_or_on_success(self):
        """测试成功结果的unwrap_or"""
        result = Result.success(42)
        value = result.unwrap_or(0)
        self.assertEqual(value, 42)
    
    def test_unwrap_or_on_failure(self):
        """测试失败结果的unwrap_or"""
        result = Result.failure("Error")
        value = result.unwrap_or(0)
        self.assertEqual(value, 0)
    
    def test_unwrap_or_else_on_success(self):
        """测试成功结果的unwrap_or_else"""
        result = Result.success(42)
        value = result.unwrap_or_else(lambda e: 0)
        self.assertEqual(value, 42)
    
    def test_unwrap_or_else_on_failure(self):
        """测试失败结果的unwrap_or_else"""
        result = Result.failure("Error")
        value = result.unwrap_or_else(lambda e: len(e))
        self.assertEqual(value, 5)
    
    def test_repr_success(self):
        """测试成功结果的字符串表示"""
        result = Result.success(42)
        self.assertEqual(repr(result), "Result.success(42)")
    
    def test_repr_failure(self):
        """测试失败结果的字符串表示"""
        result = Result.failure("Error")
        self.assertEqual(repr(result), "Result.failure('Error')")
    
    def test_chaining_operations(self):
        """测试链式操作"""
        result = (Result.success(10)
                 .map(lambda x: x * 2)
                 .map(lambda x: x + 5)
                 .flat_map(lambda x: Result.success(x / 5)))
        
        self.assertTrue(result.is_success)
        self.assertEqual(result.value, 5.0)
    
    def test_chaining_with_failure(self):
        """测试包含失败的链式操作"""
        result = (Result.success(10)
                 .map(lambda x: x * 2)
                 .flat_map(lambda x: Result.failure("Stopped"))
                 .map(lambda x: x + 5))
        
        self.assertTrue(result.is_failure)
        self.assertEqual(result.error, "Stopped")


if __name__ == '__main__':
    print("🧪 测试 Result 函数式错误处理")
    print("=" * 70)
    unittest.main(verbosity=2)
