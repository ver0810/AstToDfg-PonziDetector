#!/usr/bin/env python3
"""
配置管理器单元测试
测试配置文件加载和管理功能
"""

import sys
import os
import json
import tempfile
import unittest
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config_manager import (
    LLMProviderConfig,
    DetectionConfig,
    DFGConfig,
    OutputConfig,
    PipelineConfig
)


class TestLLMProviderConfig(unittest.TestCase):
    """LLM提供商配置测试"""
    
    def test_default_creation(self):
        """测试默认配置创建"""
        config = LLMProviderConfig()
        self.assertEqual(config.name, "qwen")
        self.assertIsNone(config.api_key)
        self.assertIsNone(config.base_url)
        self.assertIsNone(config.model)
    
    def test_custom_creation(self):
        """测试自定义配置创建"""
        config = LLMProviderConfig(
            name="openai",
            api_key="test-key",
            base_url="https://api.test.com",
            model="gpt-4"
        )
        self.assertEqual(config.name, "openai")
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.base_url, "https://api.test.com")
        self.assertEqual(config.model, "gpt-4")
    
    def test_load_from_env_qwen(self):
        """测试从环境变量加载Qwen配置"""
        os.environ["LLM_API_KEY"] = "test-key"
        os.environ["LLM_MODEL"] = "qwen-turbo"
        
        config = LLMProviderConfig(name="qwen")
        config.load_from_env()
        
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.model, "qwen-turbo")
        self.assertEqual(config.base_url, "https://dashscope.aliyuncs.com/compatible-mode/v1")
        
        # Clean up
        del os.environ["LLM_API_KEY"]
        del os.environ["LLM_MODEL"]
    
    def test_load_from_env_deepseek(self):
        """测试从环境变量加载DeepSeek配置"""
        config = LLMProviderConfig(name="deepseek")
        config.load_from_env()
        
        self.assertEqual(config.base_url, "https://api.deepseek.com")
        self.assertEqual(config.model, "deepseek-chat")
    
    def test_load_from_env_openai(self):
        """测试从环境变量加载OpenAI配置"""
        config = LLMProviderConfig(name="openai")
        config.load_from_env()
        
        self.assertEqual(config.base_url, "https://api.openai.com/v1")
        self.assertEqual(config.model, "gpt-4")


class TestDetectionConfig(unittest.TestCase):
    """检测配置测试"""
    
    def test_default_creation(self):
        """测试默认配置创建"""
        config = DetectionConfig()
        self.assertFalse(config.enabled)
        self.assertEqual(config.concurrency_limit, 40)
        self.assertTrue(config.cache_enabled)
        self.assertEqual(config.cache_dir, "cache")
        self.assertEqual(config.timeout, 60)
        self.assertEqual(config.max_retries, 3)
        self.assertIsInstance(config.provider, LLMProviderConfig)
    
    def test_custom_creation(self):
        """测试自定义配置创建"""
        provider = LLMProviderConfig(name="openai", api_key="test")
        config = DetectionConfig(
            enabled=True,
            concurrency_limit=20,
            cache_enabled=False,
            provider=provider
        )
        self.assertTrue(config.enabled)
        self.assertEqual(config.concurrency_limit, 20)
        self.assertFalse(config.cache_enabled)
        self.assertEqual(config.provider.name, "openai")


class TestDFGConfig(unittest.TestCase):
    """DFG配置测试"""
    
    def test_default_creation(self):
        """测试默认配置创建"""
        config = DFGConfig()
        self.assertEqual(config.mode, "standard")
        self.assertIsInstance(config.include_types, list)
        self.assertIn("contract_definition", config.include_types)
        self.assertIn("function_definition", config.include_types)
    
    def test_edge_types(self):
        """测试边类型配置"""
        config = DFGConfig()
        self.assertIn("data_dependency", config.edge_types)
        self.assertIn("control_flow", config.edge_types)
        self.assertIn("call", config.edge_types)


class TestOutputConfig(unittest.TestCase):
    """输出配置测试"""
    
    def test_default_creation(self):
        """测试默认配置创建"""
        config = OutputConfig()
        self.assertEqual(config.format, "json")
        self.assertEqual(config.output_dir, "output")
        self.assertTrue(config.prettify)
        self.assertTrue(config.include_metadata)
        self.assertFalse(config.include_source_code)


class TestPipelineConfig(unittest.TestCase):
    """流水线配置测试"""
    
    def test_default_creation(self):
        """测试默认配置创建"""
        config = PipelineConfig()
        self.assertEqual(config.solidity_version, "0.4.x")
        self.assertIsInstance(config.dfg, DFGConfig)
        self.assertIsInstance(config.detection, DetectionConfig)
        self.assertIsInstance(config.output, OutputConfig)
        self.assertFalse(config.verbose)
    
    def test_load_from_file(self):
        """测试从文件加载配置"""
        # 创建临时配置文件
        config_data = {
            "solidity_version": "0.8.x",
            "dfg": {
                "mode": "compact"
            },
            "detection": {
                "enabled": True,
                "concurrency_limit": 20,
                "provider": {
                    "name": "openai",
                    "api_key": "test-key"
                }
            },
            "output": {
                "output_dir": "custom_output"
            },
            "verbose": True
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = PipelineConfig.load_from_file(temp_path)
            self.assertEqual(config.solidity_version, "0.8.x")
            self.assertEqual(config.dfg.mode, "compact")
            self.assertTrue(config.detection.enabled)
            self.assertEqual(config.detection.concurrency_limit, 20)
            self.assertEqual(config.output.output_dir, "custom_output")
            self.assertTrue(config.verbose)
        finally:
            os.unlink(temp_path)
    
    def test_load_from_nonexistent_file(self):
        """测试从不存在的文件加载配置"""
        with self.assertRaises(FileNotFoundError):
            PipelineConfig.load_from_file("nonexistent.json")
    
    def test_save_to_file(self):
        """测试保存配置到文件"""
        config = PipelineConfig(
            solidity_version="0.8.x",
            verbose=True
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            config.save_to_file(temp_path)
            
            # 验证文件存在且可以读取
            self.assertTrue(os.path.exists(temp_path))
            
            with open(temp_path, 'r') as f:
                data = json.load(f)
                self.assertEqual(data['solidity_version'], "0.8.x")
                self.assertTrue(data['verbose'])
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    def test_load_from_args(self):
        """测试从命令行参数加载"""
        from argparse import Namespace
        
        args = Namespace(
            config=None,
            detect=True,
            mode='compact',
            output='custom_output',
            api_key='new-key',
            concurrency=30,
            verbose=True,
            base_url=None,
            model=None,
            llm_provider='qwen'
        )
        
        config = PipelineConfig.load_from_args(args)
        
        self.assertTrue(config.detection.enabled)
        self.assertEqual(config.dfg.mode, 'compact')
        self.assertEqual(config.output.output_dir, 'custom_output')
        self.assertEqual(config.detection.provider.api_key, 'new-key')
        self.assertEqual(config.detection.concurrency_limit, 30)
        self.assertTrue(config.verbose)
        self.assertEqual(config.detection.provider.name, 'qwen')


if __name__ == '__main__':
    print("🧪 测试配置管理器")
    print("=" * 70)
    unittest.main(verbosity=2)
