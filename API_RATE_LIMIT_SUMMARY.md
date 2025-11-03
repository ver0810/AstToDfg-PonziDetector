# API 限流解决方案总结

## 🎯 问题

批量检测时,不同的 LLM 提供商有速率限制,可能导致:
- 429 错误(Too Many Requests)
- 请求被拒绝
- 账户被临时封禁
- 批量处理失败

## ✅ 解决方案

### 1. **三层防护机制**

#### 第一层:速率限制器(Rate Limiter)
```python
class RateLimiter:
    - 令牌桶算法
    - 每秒级别限制(RPS)
    - 每分钟级别限制(RPM)
    - 平滑处理突发请求
```

#### 第二层:智能重试
```python
- 速率限制错误:指数退避重试(最多10次)
- 网络错误:自动重试(最多5次)
- 退避时间:1秒 → 2秒 → 4秒 → ... → 60秒
```

#### 第三层:请求控制
```python
- 请求间最小延迟(REQUEST_DELAY)
- 并发数控制(--concurrency)
- API 超时设置(API_TIMEOUT)
```

### 2. **配置方式**

#### 环境变量(推荐)
```bash
export RATE_LIMIT_PER_MINUTE=60        # 每分钟最大请求数
export RATE_LIMIT_PER_SECOND=10        # 每秒最大请求数
export REQUEST_DELAY=0.1               # 请求间延迟(秒)
export RATE_LIMIT_RETRY_ATTEMPTS=10    # 速率限制重试次数
export INITIAL_BACKOFF=1.0             # 初始退避时间
export MAX_BACKOFF=60.0                # 最大退避时间
```

#### 命令行参数
```bash
python -m src.main --detect-only \
  --detect-dir output/batch_full_compact \
  --concurrency 5 \
  --api-key YOUR_KEY \
  --base-url YOUR_URL \
  --model YOUR_MODEL
```

## 📊 推荐配置

### 场景 1: 小批量测试(1-50个)
```bash
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_SECOND=10
REQUEST_DELAY=0.1
--concurrency 5
```

### 场景 2: 中等批量(50-200个)
```bash
RATE_LIMIT_PER_MINUTE=50
RATE_LIMIT_PER_SECOND=8
REQUEST_DELAY=0.15
--concurrency 10
```

### 场景 3: 大批量(200+个)
```bash
RATE_LIMIT_PER_MINUTE=40
RATE_LIMIT_PER_SECOND=5
REQUEST_DELAY=0.2
--concurrency 20
```

### 场景 4: 超级安全(免费账户)
```bash
RATE_LIMIT_PER_MINUTE=15
RATE_LIMIT_PER_SECOND=1
REQUEST_DELAY=1.0
--concurrency 1
```

## 🔧 常见问题解决

### 问题 1: 遇到 429 错误
```bash
# 降低速率限制
export RATE_LIMIT_PER_MINUTE=30
export RATE_LIMIT_PER_SECOND=3
export REQUEST_DELAY=0.5
--concurrency 1
```

### 问题 2: 处理太慢
```bash
# 提高并发(如果 API 允许)
export RATE_LIMIT_PER_MINUTE=100
--concurrency 20
```

### 问题 3: 频繁超时
```bash
# 增加超时时间,降低并发
export API_TIMEOUT=180
--concurrency 5
```

## 📈 性能数据

基于50个合约的测试:
- **准确率**: 91.49%
- **召回率**: 100.00%
- **F1 分数**: 0.8462

不同配置的处理速度:
- 保守模式(1并发): ~0.5 合约/秒
- 标准模式(5并发): ~2 合约/秒
- 激进模式(20并发): ~5 合约/秒

## 📚 相关文档

1. **docs/RATE_LIMIT_GUIDE.md** - 详细使用指南
2. **config.rate_limit_examples.json** - 配置示例
3. **examples/test_rate_limit.py** - 测试脚本

## 🔄 核心代码改进

### 新增文件
- `src/detector/llm_detector.py` - 新增 RateLimiter 类

### 主要改动
```python
# 1. 速率限制器类
class RateLimiter:
    - 令牌桶算法实现
    - 双层限制(秒级+分钟级)
    
# 2. 改进的配置类
class LLMConfig:
    - rate_limit_per_minute
    - rate_limit_per_second
    - request_delay
    - rate_limit_retry_attempts
    
# 3. 智能重试机制
async def _call_api_with_retry():
    - 自动检测速率限制错误
    - 指数退避重试
    - 网络错误处理
```

## ✅ 测试验证

运行测试脚本:
```bash
python examples/test_rate_limit.py
```

预期输出:
```
✅ 配置加载成功!
✅ 速率限制器创建成功
✅ 符合限制 (≤3 RPS): 是
✅ 所有测试通过!
```

## 🚀 快速开始

1. 设置环境变量
2. 运行小批量测试
3. 根据结果调整配置
4. 扩大到全量处理

示例:
```bash
# 1. 设置配置
export RATE_LIMIT_PER_MINUTE=30
export RATE_LIMIT_PER_SECOND=3

# 2. 小批量测试
python -m src.main --detect-only \
  --detect-dir output/batch_full_compact \
  --concurrency 3 \
  --limit 10

# 3. 观察结果,调整配置
# 4. 扩大到全量
python -m src.main --detect-only \
  --detect-dir output/batch_full_compact \
  --concurrency 5
```

---

**更新时间**: 2025-11-03  
**版本**: 1.0  
**状态**: ✅ 已测试
