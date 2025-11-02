#!/usr/bin/env python3
"""
数据集加载器单元测试
测试数据集加载和处理功能
"""

import sys
import json
import tempfile
import os
import unittest
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.dataset_loader import DatasetLoader
from src.utils.result import Result


class TestDatasetLoader(unittest.TestCase):
    """数据集加载器测试"""
    
    def setUp(self):
        """测试前准备"""
        self.loader = DatasetLoader()
    
    def test_load_valid_json_dataset(self):
        """测试加载有效JSON数据集"""
        # 创建临时数据集文件
        dataset = [
            {"code": "contract A {}", "label": 0},
            {"code": "contract B {}", "label": 1}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(dataset, f)
            temp_path = f.name
        
        try:
            result = self.loader.load_dataset(temp_path)
            
            self.assertTrue(result.is_success)
            data = result.value
            self.assertEqual(len(data), 2)
            self.assertIn("code", data[0])
            self.assertIn("label", data[0])
        finally:
            os.unlink(temp_path)
    
    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        result = self.loader.load_dataset("nonexistent_file.json")
        
        self.assertTrue(result.is_failure)
        self.assertIn("not found", result.error.lower())
    
    def test_load_invalid_json(self):
        """测试加载无效JSON"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json")
            temp_path = f.name
        
        try:
            result = self.loader.load_dataset(temp_path)
            self.assertTrue(result.is_failure)
        finally:
            os.unlink(temp_path)
    
    def test_load_dataset_with_limit(self):
        """测试限制加载数量"""
        dataset = [
            {"code": f"contract C{i} {{}}", "label": i % 2}
            for i in range(100)
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(dataset, f)
            temp_path = f.name
        
        try:
            result = self.loader.load_dataset(temp_path, limit=10)
            
            self.assertTrue(result.is_success)
            data = result.value
            self.assertEqual(len(data), 10)
        finally:
            os.unlink(temp_path)
    
    def test_validate_dataset_structure(self):
        """测试验证数据集结构"""
        # 有效数据集
        valid_dataset = [
            {"code": "contract A {}"},
            {"code": "contract B {}"}
        ]
        
        result = self.loader.validate_dataset(valid_dataset)
        self.assertTrue(result.is_success)
        
        # 无效数据集 - 缺少code字段
        invalid_dataset = [
            {"label": 0},
            {"code": "contract B {}"}
        ]
        
        result = self.loader.validate_dataset(invalid_dataset)
        self.assertTrue(result.is_failure)
    
    def test_extract_codes(self):
        """测试提取代码"""
        dataset = [
            {"code": "contract A {}", "label": 0},
            {"code": "contract B {}", "label": 1},
            {"code": "contract C {}", "label": 0}
        ]
        
        codes = self.loader.extract_codes(dataset)
        
        self.assertEqual(len(codes), 3)
        self.assertEqual(codes[0], "contract A {}")
        self.assertEqual(codes[1], "contract B {}")
    
    def test_extract_labels(self):
        """测试提取标签"""
        dataset = [
            {"code": "contract A {}", "label": 0},
            {"code": "contract B {}", "label": 1},
            {"code": "contract C {}"}  # 没有标签
        ]
        
        labels = self.loader.extract_labels(dataset)
        
        self.assertEqual(len(labels), 3)
        self.assertEqual(labels[0], 0)
        self.assertEqual(labels[1], 1)
        self.assertIsNone(labels[2])
    
    def test_filter_by_label(self):
        """测试按标签过滤"""
        dataset = [
            {"code": "contract A {}", "label": 0},
            {"code": "contract B {}", "label": 1},
            {"code": "contract C {}", "label": 0},
            {"code": "contract D {}", "label": 1}
        ]
        
        # 过滤标签为0的
        filtered = self.loader.filter_by_label(dataset, 0)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["code"], "contract A {}")
        self.assertEqual(filtered[1]["code"], "contract C {}")
        
        # 过滤标签为1的
        filtered = self.loader.filter_by_label(dataset, 1)
        self.assertEqual(len(filtered), 2)


class TestDatasetLoaderIntegration(unittest.TestCase):
    """数据集加载器集成测试"""
    
    def test_complete_workflow(self):
        """测试完整工作流"""
        # 创建测试数据集
        dataset = [
            {"code": f"contract Test{i} {{}}", "label": i % 2}
            for i in range(20)
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(dataset, f)
            temp_path = f.name
        
        try:
            loader = DatasetLoader()
            
            # 加载数据集
            result = loader.load_dataset(temp_path, limit=10)
            self.assertTrue(result.is_success)
            
            data = result.value
            
            # 验证数据集
            validation = loader.validate_dataset(data)
            self.assertTrue(validation.is_success)
            
            # 提取代码和标签
            codes = loader.extract_codes(data)
            labels = loader.extract_labels(data)
            
            self.assertEqual(len(codes), 10)
            self.assertEqual(len(labels), 10)
            
            # 按标签过滤
            label_0 = loader.filter_by_label(data, 0)
            label_1 = loader.filter_by_label(data, 1)
            
            self.assertEqual(len(label_0) + len(label_1), 10)
            
        finally:
            os.unlink(temp_path)
    
    def test_large_dataset_handling(self):
        """测试大数据集处理"""
        # 创建大数据集
        dataset = [
            {"code": f"contract C{i} {{}}", "label": i % 3}
            for i in range(1000)
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(dataset, f)
            temp_path = f.name
        
        try:
            loader = DatasetLoader()
            
            # 不限制
            result = loader.load_dataset(temp_path)
            self.assertTrue(result.is_success)
            self.assertEqual(len(result.value), 1000)
            
            # 限制100条
            result = loader.load_dataset(temp_path, limit=100)
            self.assertTrue(result.is_success)
            self.assertEqual(len(result.value), 100)
            
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    print("🧪 测试数据集加载器")
    print("=" * 70)
    unittest.main(verbosity=2)
