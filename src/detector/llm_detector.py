#!/usr/bin/env python3
"""
LLM-based Ponzi scheme detection pipeline.
Asynchronous implementation for efficient batch processing.
"""

import json
import os
import asyncio
import hashlib
import time
from typing import Dict, Optional
from dataclasses import dataclass
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from asyncio import Semaphore

from ..utils.functional_helpers import Result


@dataclass
class ClassificationResult:
    """Classification result from the model"""
    is_ponzi: bool
    confidence: float
    risk_level: str
    reasoning: str


class RateLimiter:
    """
    异步速率限制器，用于控制 API 调用频率
    支持令牌桶算法，平滑处理突发请求
    """
    
    def __init__(self, calls_per_minute: int = 60, calls_per_second: int = 10):
        """
        初始化速率限制器
        
        Args:
            calls_per_minute: 每分钟最大请求数
            calls_per_second: 每秒最大请求数
        """
        self.calls_per_minute = calls_per_minute
        self.calls_per_second = calls_per_second
        
        # 令牌桶 - 每秒级别
        self.second_tokens = calls_per_second
        self.second_max_tokens = calls_per_second
        self.second_last_update = time.time()
        
        # 令牌桶 - 每分钟级别
        self.minute_tokens = calls_per_minute
        self.minute_max_tokens = calls_per_minute
        self.minute_last_update = time.time()
        
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """获取一个令牌，如果没有可用令牌则等待"""
        async with self._lock:
            while True:
                now = time.time()
                
                # 更新每秒令牌
                time_passed = now - self.second_last_update
                self.second_tokens = min(
                    self.second_max_tokens,
                    self.second_tokens + time_passed * self.calls_per_second
                )
                self.second_last_update = now
                
                # 更新每分钟令牌
                time_passed_minute = now - self.minute_last_update
                self.minute_tokens = min(
                    self.minute_max_tokens,
                    self.minute_tokens + time_passed_minute * (self.calls_per_minute / 60.0)
                )
                self.minute_last_update = now
                
                # 检查是否有足够的令牌
                if self.second_tokens >= 1 and self.minute_tokens >= 1:
                    self.second_tokens -= 1
                    self.minute_tokens -= 1
                    return
                
                # 计算需要等待的时间
                wait_time_second = (1 - self.second_tokens) / self.calls_per_second if self.second_tokens < 1 else 0
                wait_time_minute = (1 - self.minute_tokens) / (self.calls_per_minute / 60.0) if self.minute_tokens < 1 else 0
                wait_time = max(wait_time_second, wait_time_minute, 0.1)
                
                await asyncio.sleep(wait_time)


class LLMConfig:
    """Configuration for LLM API"""
    
    def __init__(self, api_key: str = None, base_url: str = None, model: str = None,
                 rate_limit_per_minute: int = None, rate_limit_per_second: int = None,
                 request_delay: float = None):
        # Use environment variables as defaults
        self.api_key = api_key or os.getenv('OPENAI_API_KEY', 'sk-8e71e4eb5d1d4471aed912b4e4172cb1')
        self.base_url = base_url or os.getenv('OPENAI_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
        self.model = model or os.getenv('OPENAI_MODEL', 'qwen-plus')
        
        # Rate limiting configuration
        self.rate_limit_per_minute = rate_limit_per_minute or int(os.getenv('RATE_LIMIT_PER_MINUTE', '60'))
        self.rate_limit_per_second = rate_limit_per_second or int(os.getenv('RATE_LIMIT_PER_SECOND', '10'))
        self.request_delay = request_delay or float(os.getenv('REQUEST_DELAY', '0.1'))  # 请求间最小延迟（秒）
        
        # Retry configuration
        self.retry_attempts = int(os.getenv('RETRY_ATTEMPTS', '5'))  # 增加重试次数
        self.timeout = int(os.getenv('API_TIMEOUT', '120'))
        
        # Backoff configuration for rate limit errors
        self.rate_limit_retry_attempts = int(os.getenv('RATE_LIMIT_RETRY_ATTEMPTS', '10'))
        self.initial_backoff = float(os.getenv('INITIAL_BACKOFF', '1.0'))
        self.max_backoff = float(os.getenv('MAX_BACKOFF', '60.0'))


class StaticAnalyzer:
    """Static analyzer model - analyzes contract code/DFG"""
    
    def __init__(self, config: LLMConfig, client: AsyncOpenAI, rate_limiter: RateLimiter = None):
        self.config = config
        self.client = client
        self.rate_limiter = rate_limiter
        self.system_prompt = """你是一名区块链智能合约风险审计专家，分析庞氏骗局、资金盘及高风险投资合约。

目标：准确分类风险。输入为结构化JSON格式数据流图。

请严格按照以下结构，仅输出JSON格式，不包含其他文字内容，JSON结构如下：
```json
{
    "is_ponzi": true/false,
    "confidence": 0~1,
    "risk_level": "高" | "中" | "低",
    "reasoning": ""
}
```
"""
    
    async def _call_api_with_retry(self, contract_data: str, retry_count: int = 0) -> str:
        """
        调用 API 并处理速率限制错误
        
        Args:
            contract_data: 合约数据
            retry_count: 当前重试次数
            
        Returns:
            API 响应内容
        """
        # 使用速率限制器
        if self.rate_limiter:
            await self.rate_limiter.acquire()
        
        # 添加请求间延迟
        if self.config.request_delay > 0:
            await asyncio.sleep(self.config.request_delay)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                extra_body={"enable_thinking": False},
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"请分析以下智能合约数据：\n ```json{contract_data}```"}
                ],
                timeout=self.config.timeout,
                temperature=0
            )
            return response.choices[0].message.content
            
        except Exception as e:
            error_str = str(e)
            
            # 检查是否是速率限制错误
            if "429" in error_str or "rate limit" in error_str.lower() or "too many requests" in error_str.lower():
                if retry_count < self.config.rate_limit_retry_attempts:
                    # 指数退避
                    backoff = min(
                        self.config.initial_backoff * (2 ** retry_count),
                        self.config.max_backoff
                    )
                    print(f"⚠️  遇到速率限制，等待 {backoff:.1f} 秒后重试（第 {retry_count + 1}/{self.config.rate_limit_retry_attempts} 次）")
                    await asyncio.sleep(backoff)
                    return await self._call_api_with_retry(contract_data, retry_count + 1)
                else:
                    raise Exception(f"达到速率限制重试上限: {error_str}")
            
            # 检查是否是连接或超时错误
            elif any(err in error_str.lower() for err in ["timeout", "connection", "network"]):
                if retry_count < self.config.retry_attempts:
                    backoff = min(2 ** retry_count, 10)
                    print(f"⚠️  网络错误，等待 {backoff:.1f} 秒后重试: {error_str}")
                    await asyncio.sleep(backoff)
                    return await self._call_api_with_retry(contract_data, retry_count + 1)
                else:
                    raise Exception(f"达到网络错误重试上限: {error_str}")
            
            # 其他错误直接抛出
            raise
    
    async def analyze_code(self, contract_data: str) -> ClassificationResult:
        """Analyze contract code/DFG and generate report"""
        try:
            # 使用带重试的 API 调用
            content = await self._call_api_with_retry(contract_data)
            
            if not content:
                print(f"⚠️ API 返回空内容")
                return ClassificationResult(False, 0.0, "未知", "API返回空内容")
            
            # 尝试提取 JSON 内容
            # LLM 可能返回带有解释的文本，我们需要提取 JSON 部分
            import re
            
            # 尝试找到 JSON 代码块
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试找到直接的 JSON 对象
                json_match = re.search(r'(\{[^{}]*"is_ponzi"[^{}]*\})', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    # 如果找不到 JSON，尝试直接解析整个内容
                    json_str = content.strip()
            
            # 解析 JSON
            try:
                result_json = json.loads(json_str)
            except json.JSONDecodeError as je:
                print(f"⚠️ JSON 解析失败，原始内容: {content[:200]}...")
                print(f"   错误: {je}")
                # 返回默认结果，但保留原始响应作为理由
                return ClassificationResult(
                    is_ponzi=False,
                    confidence=0.0,
                    risk_level="未知",
                    reasoning=f"JSON解析失败，原始响应: {content[:500]}"
                )
            
            return ClassificationResult(
                is_ponzi=bool(result_json.get("is_ponzi", False)),
                confidence=float(result_json.get("confidence", 0.0)),
                risk_level=result_json.get("risk_level", "未知"),
                reasoning=result_json.get("reasoning", "无详细理由。")
            )
            
        except Exception as e:
            print(f"❌ 模型分析失败: {e}")
            import traceback
            traceback.print_exc()
            return ClassificationResult(False, 0.0, "未知", f"分类异常: {str(e)}")

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
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(
            calls_per_minute=self.config.rate_limit_per_minute,
            calls_per_second=self.config.rate_limit_per_second
        )
        
        # Initialize models with rate limiter
        self.analyzer = StaticAnalyzer(self.config, self.client, self.rate_limiter)
        
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
            result = await self.analyzer.analyze_code(contract_data)
            report_str = result.reasoning
            
        except Exception as e:
            print(f"检测失败 {contract_name}: {e}")
            report_str = "分析失败"
            result = ClassificationResult(False, 0.0, "未知", f"异常: {str(e)}")
        
        result_dict = {
            "contract_name": contract_name,
            # "analysis_report": report_str,
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
