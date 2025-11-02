#!/usr/bin/env python3
"""
功能性帮助函数单元测试
测试函数式编程辅助功能
"""

import sys
import unittest
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.result import Result
from src.utils.functional_helpers import (
    safe_divide,
    safe_file_read,
    safe_json_parse,
    safe_dict_get,
    chain_results,
    collect_results
)


class TestSafeFunctions(unittest.TestCase):
    """安全函数测试"""
    
    def test_safe_divide_success(self):
        """测试安全除法成功情况"""
        result = safe_divide(10, 2)
        self.assertTrue(result.is_success)
        self.assertEqual(result.value, 5.0)
    
    def test_safe_divide_by_zero(self):
        """测试除以零"""
        result = safe_divide(10, 0)
        self.assertTrue(result.is_failure)
        self.assertIn("zero", result.error.lower())
    
    def test_safe_dict_get_existing_key(self):
        """测试安全获取存在的字典键"""
        data = {"name": "test", "value": 42}
        result = safe_dict_get(data, "name")
        
        self.assertTrue(result.is_success)
        self.assertEqual(result.value, "test")
    
    def test_safe_dict_get_missing_key(self):
        """测试安全获取不存在的字典键"""
        data = {"name": "test"}
        result = safe_dict_get(data, "value")
        
        self.assertTrue(result.is_failure)
        self.assertIn("not found", result.error.lower())
    
    def test_safe_dict_get_nested(self):
        """测试安全获取嵌套字典"""
        data = {"user": {"profile": {"name": "Alice"}}}
        result = safe_dict_get(data, "user.profile.name", delimiter=".")
        
        self.assertTrue(result.is_success)
        self.assertEqual(result.value, "Alice")
    
    def test_safe_json_parse_valid(self):
        """测试解析有效JSON"""
        json_str = '{"name": "test", "value": 42}'
        result = safe_json_parse(json_str)
        
        self.assertTrue(result.is_success)
        self.assertEqual(result.value["name"], "test")
        self.assertEqual(result.value["value"], 42)
    
    def test_safe_json_parse_invalid(self):
        """测试解析无效JSON"""
        json_str = '{"name": invalid}'
        result = safe_json_parse(json_str)
        
        self.assertTrue(result.is_failure)


class TestResultChaining(unittest.TestCase):
    """Result链式操作测试"""
    
    def test_chain_results_all_success(self):
        """测试链式操作全部成功"""
        results = [
            Result.success(1),
            Result.success(2),
            Result.success(3)
        ]
        
        final = chain_results(results, lambda values: sum(values))
        
        self.assertTrue(final.is_success)
        self.assertEqual(final.value, 6)
    
    def test_chain_results_with_failure(self):
        """测试链式操作包含失败"""
        results = [
            Result.success(1),
            Result.failure("Error"),
            Result.success(3)
        ]
        
        final = chain_results(results, lambda values: sum(values))
        
        self.assertTrue(final.is_failure)
    
    def test_collect_results_all_success(self):
        """测试收集所有成功结果"""
        results = [
            Result.success(1),
            Result.success(2),
            Result.success(3)
        ]
        
        collected = collect_results(results)
        
        self.assertTrue(collected.is_success)
        self.assertEqual(len(collected.value), 3)
        self.assertEqual(collected.value, [1, 2, 3])
    
    def test_collect_results_with_failures(self):
        """测试收集结果包含失败"""
        results = [
            Result.success(1),
            Result.failure("Error 1"),
            Result.success(3),
            Result.failure("Error 2")
        ]
        
        collected = collect_results(results)
        
        self.assertTrue(collected.is_failure)
        self.assertIn("Error 1", collected.error)


if __name__ == '__main__':
    print("🧪 测试功能性帮助函数")
    print("=" * 70)
    unittest.main(verbosity=2)
