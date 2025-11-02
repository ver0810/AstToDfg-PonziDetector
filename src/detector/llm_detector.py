#!/usr/bin/env python3
"""
LLM-based Ponzi scheme detection pipeline.
Asynchronous implementation for efficient batch processing.
"""

import json
import os
import asyncio
import hashlib
from typing import Dict, Optional
from dataclasses import dataclass
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..utils.functional_helpers import Result


@dataclass
class ClassificationResult:
    """Classification result from the model"""
    is_ponzi: bool
    confidence: float
    risk_level: str
    reasoning: str


class LLMConfig:
    """Configuration for LLM API"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None):
        # Use environment variables as defaults
        self.api_key = api_key or os.getenv('OPENAI_API_KEY', 'sk-8e71e4eb5d1d4471aed912b4e4172cb1')
        self.base_url = base_url or os.getenv('OPENAI_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        self.model = model or os.getenv('OPENAI_MODEL', 'qwen-plus')
        
        # Retry configuration
        self.retry_attempts = int(os.getenv('RETRY_ATTEMPTS', '3'))
        self.timeout = int(os.getenv('API_TIMEOUT', '120'))


class StaticAnalyzer:
    """Static analyzer model - analyzes contract code/DFG"""
    
    def __init__(self, config: LLMConfig, client: AsyncOpenAI):
        self.config = config
        self.client = client
        self.system_prompt = """你是一名区块链智能合约风险审计专家，分析庞氏骗局、资金盘及高风险投资合约。

目标：准确分类风险。输入为结构化JSON格式数据流图。

请严格按照以下结构，输出JSON格式，结构如下：
```json
{
    "is_ponzi": true/false,
    "confidence": 0~1,
    "risk_level": "高" | "中" | "低",
    "reasoning": ""
}
```
"""
    
    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=10),
        reraise=True
    )
    async def analyze_code(self, contract_data: str) -> str:
        """Analyze contract code/DFG and generate report"""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"请分析以下智能合约数据：\n{contract_data}"}
                ],
                timeout=self.config.timeout,
                temperature=0
            )
            content = response.choices[0].message.content
            return content if content else "分析失败：API未返回内容"
        except Exception as e:
            print(f"模型分析失败: {e}")
            return "分析失败"


class Classifier:
    """Classifier model - classifies based on analysis report"""
    
    def __init__(self, config: LLMConfig, client: AsyncOpenAI):
        self.config = config
        self.client = client
        self.system_prompt = """你是一个智能合约安全分类专家。请根据分析报告判断是否为庞氏骗局。

输出格式为JSON，包含以下字段：
- is_ponzi: 布尔值 (true/false)
- confidence: 浮点数 (0.0到1.0)
- risk_level: 字符串 ("高", "中", "低")
- reasoning: 字符串 (简要说明判断依据)

请只返回JSON对象。"""
    
    @retry(
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, max=10),
        reraise=True
    )
    async def classify(self, analysis_report: str) -> ClassificationResult:
        """Classify based on analysis report"""
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"请根据以下分析报告进行分类：\n{analysis_report}"}
                ],
                response_format={"type": "json_object"},
                temperature=0,
                timeout=60,
            )
            result_json = json.loads(response.choices[0].message.content)
            return ClassificationResult(
                is_ponzi=bool(result_json.get("is_ponzi", False)),
                confidence=float(result_json.get("confidence", 0.0)),
                risk_level=result_json.get("risk_level", "未知"),
                reasoning=result_json.get("reasoning", "无详细理由。")
            )
        except Exception as e:
            print(f"模型分类失败: {e}")
            return ClassificationResult(False, 0.0, "未知", "分类异常")


class PonziDetectionPipeline:
    """Ponzi detection pipeline using LLM cascade"""
    
    def __init__(self, config: LLMConfig = None, cache_dir: str = "cache"):
        self.config = config or LLMConfig()
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize async client
        self.client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        # Initialize models
        self.analyzer = StaticAnalyzer(self.config, self.client)
        self.classifier = Classifier(self.config, self.client)
        
        # Cache
        self.cache = {}
        self.cache_file = os.path.join(cache_dir, "detection_cache.json")
        self._load_cache()
    
    def _load_cache(self):
        """Load cache from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
            except Exception as e:
                print(f"加载缓存失败: {e}")
                self.cache = {}
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存缓存失败: {e}")
    
    def _get_code_hash(self, code: str) -> str:
        """Generate hash for code"""
        return hashlib.md5(code.encode('utf-8')).hexdigest()
    
    async def detect(self, contract_data: str, contract_name: str = "Unknown") -> Dict:
        """
        Detect if contract is a Ponzi scheme.
        
        Args:
            contract_data: Contract code or DFG JSON string
            contract_name: Name of the contract
            
        Returns:
            Detection result dictionary
        """
        code_hash = self._get_code_hash(contract_data)
        
        # Check cache
        if code_hash in self.cache:
            cached_item = self.cache[code_hash]
            if "analysis_report" in cached_item and "classification_result" in cached_item:
                print(f"缓存命中: {contract_name}")
                return cached_item
        
        try:
            # Step 1: Analyze contract data
            report_str = await self.analyzer.analyze_code(contract_data)
            if "分析失败" in report_str:
                raise Exception("分析报告生成失败")
            
            # Step 2: Classify based on report
            result = await self.classifier.classify(report_str)
            
        except Exception as e:
            print(f"检测失败 {contract_name}: {e}")
            report_str = "分析失败"
            result = ClassificationResult(False, 0.0, "未知", f"异常: {str(e)}")
        
        result_dict = {
            "contract_name": contract_name,
            "analysis_report": report_str,
            "classification_result": {
                "is_ponzi": result.is_ponzi,
                "confidence": result.confidence,
                "risk_level": result.risk_level,
                "reasoning": result.reasoning
            },
            "code_hash": code_hash
        }
        
        # Save to cache
        self.cache[code_hash] = result_dict
        self._save_cache()
        
        return result_dict
    
    async def detect_from_json_file(self, json_file_path: str) -> Dict:
        """
        Detect from a JSON file (DFG output).
        
        Args:
            json_file_path: Path to JSON file
            
        Returns:
            Detection result
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert JSON to string for analysis
            contract_data = json.dumps(data, indent=2, ensure_ascii=False)
            contract_name = os.path.basename(json_file_path).replace('.json', '')
            
            return await self.detect(contract_data, contract_name)
            
        except Exception as e:
            return {
                "contract_name": os.path.basename(json_file_path),
                "error": str(e),
                "classification_result": {
                    "is_ponzi": False,
                    "confidence": 0.0,
                    "risk_level": "未知",
                    "reasoning": f"文件读取失败: {str(e)}"
                }
            }
