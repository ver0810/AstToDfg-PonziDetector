#!/usr/bin/env python3
"""
API 限流功能测试和演示脚本
展示如何使用不同的速率限制配置
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

def print_section(title):
    """打印分隔线"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def test_config_loading():
    """测试配置加载"""
    print_section("测试 1: 配置加载")
    
    # 设置环境变量
    os.environ['RATE_LIMIT_PER_MINUTE'] = '30'
    os.environ['RATE_LIMIT_PER_SECOND'] = '3'
    os.environ['REQUEST_DELAY'] = '0.5'
    os.environ['RATE_LIMIT_RETRY_ATTEMPTS'] = '8'
    os.environ['INITIAL_BACKOFF'] = '2.0'
    os.environ['MAX_BACKOFF'] = '30.0'
    
    try:
        from src.detector.llm_detector import LLMConfig
        
        config = LLMConfig()
        print("✅ 配置加载成功！")
        print(f"\n📋 当前配置:")
        print(f"   API Key: {config.api_key[:20]}...")
        print(f"   Base URL: {config.base_url}")
        print(f"   Model: {config.model}")
        print(f"\n⏱️  速率限制:")
        print(f"   每分钟限制: {config.rate_limit_per_minute} 请求")
        print(f"   每秒限制: {config.rate_limit_per_second} 请求")
        print(f"   请求间延迟: {config.request_delay} 秒")
        print(f"\n🔄 重试配置:")
        print(f"   速率限制重试: {config.rate_limit_retry_attempts} 次")
        print(f"   一般错误重试: {config.retry_attempts} 次")
        print(f"   初始退避时间: {config.initial_backoff} 秒")
        print(f"   最大退避时间: {config.max_backoff} 秒")
        print(f"   API 超时: {config.timeout} 秒")
        
        return True
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_rate_limiter():
    """测试速率限制器"""
    print_section("测试 2: 速率限制器")
    
    import asyncio
    import time
    
    try:
        from src.detector.llm_detector import RateLimiter
        
        # 创建限制器 (3 RPS)
        limiter = RateLimiter(calls_per_minute=180, calls_per_second=3)
        print("✅ 速率限制器创建成功")
        print(f"   配置: 每秒最多 3 个请求\n")
        
        async def simulate_requests(count=10):
            """模拟多个请求"""
            print(f"📊 模拟 {count} 个连续请求:\n")
            start = time.time()
            
            for i in range(count):
                await limiter.acquire()
                elapsed = time.time() - start
                print(f"   请求 {i+1:2d}: {elapsed:5.2f}秒 ✓")
            
            total_time = time.time() - start
            rps = count / total_time
            print(f"\n⏱️  总耗时: {total_time:.2f} 秒")
            print(f"📈 实际速率: {rps:.2f} 请求/秒")
            print(f"✅ 符合限制 (≤3 RPS): {'是' if rps <= 3.1 else '否'}")
        
        # 运行测试
        asyncio.run(simulate_requests(10))
        return True
        
    except Exception as e:
        print(f"❌ 速率限制器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_usage_examples():
    """显示使用示例"""
    print_section("使用示例")
    
    examples = [
        {
            "title": "示例 1: 小批量测试（推荐用于测试）",
            "command": """
export RATE_LIMIT_PER_MINUTE=60
export RATE_LIMIT_PER_SECOND=10
export REQUEST_DELAY=0.1

python -m src.main --detect-only \\
  --detect-dir output/batch_full_compact \\
  --concurrency 5 \\
  --limit 10 \\
  --api-key YOUR_KEY \\
  --base-url YOUR_URL \\
  --model YOUR_MODEL
"""
        },
        {
            "title": "示例 2: 保守模式（适合免费账户）",
            "command": """
export RATE_LIMIT_PER_MINUTE=20
export RATE_LIMIT_PER_SECOND=2
export REQUEST_DELAY=0.5

python -m src.main --detect-only \\
  --detect-dir output/batch_full_compact \\
  --concurrency 1 \\
  --limit 50
"""
        },
        {
            "title": "示例 3: 大批量处理（需要付费账户）",
            "command": """
export RATE_LIMIT_PER_MINUTE=100
export RATE_LIMIT_PER_SECOND=15
export REQUEST_DELAY=0.05

python -m src.main --detect-only \\
  --detect-dir output/batch_full_compact \\
  --concurrency 20
"""
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"{i}. {example['title']}")
        print(example['command'])

def show_troubleshooting():
    """显示故障排除指南"""
    print_section("故障排除")
    
    issues = [
        {
            "problem": "遇到 429 错误（Too Many Requests）",
            "solutions": [
                "降低 RATE_LIMIT_PER_MINUTE 到 20-30",
                "降低 RATE_LIMIT_PER_SECOND 到 2-3",
                "增加 REQUEST_DELAY 到 0.5-1.0",
                "降低 --concurrency 到 1-3",
                "检查账户配额是否用完"
            ]
        },
        {
            "problem": "处理速度太慢",
            "solutions": [
                "提高 RATE_LIMIT_PER_MINUTE（如果账户允许）",
                "降低 REQUEST_DELAY",
                "提高 --concurrency 参数",
                "使用 compact 输出模式减少数据量",
                "考虑升级 API 账户等级"
            ]
        },
        {
            "problem": "频繁超时错误",
            "solutions": [
                "增加 API_TIMEOUT 到 180 或更高",
                "降低 --concurrency",
                "检查网络连接",
                "使用 compact 模式减少输入大小"
            ]
        }
    ]
    
    for issue in issues:
        print(f"🔴 问题: {issue['problem']}")
        print(f"\n💡 解决方案:")
        for i, solution in enumerate(issue['solutions'], 1):
            print(f"   {i}. {solution}")
        print()

def main():
    """主函数"""
    print("\n" + "="*70)
    print("  API 限流功能测试和演示")
    print("="*70)
    
    # 测试配置
    if not test_config_loading():
        print("\n⚠️  配置测试失败，请检查 src/detector/llm_detector.py")
        return
    
    # 测试速率限制器
    if not test_rate_limiter():
        print("\n⚠️  速率限制器测试失败")
        return
    
    # 显示使用示例
    show_usage_examples()
    
    # 显示故障排除
    show_troubleshooting()
    
    print_section("测试完成")
    print("✅ 所有测试通过！")
    print("\n📖 更多信息请参考:")
    print("   - docs/RATE_LIMIT_GUIDE.md")
    print("   - config.rate_limit_examples.json")
    print()

if __name__ == "__main__":
    main()
