# API 限流解决方案指南

## 📋 概述

为了应对不同 LLM 提供商的速率限制，本系统实现了完善的限流和重试机制，确保批量检测时不会因为 API 限流而失败。

## 🎯 核心功能

### 1. **多层速率限制**
- **每秒限制**: 控制每秒最大请求数
- **每分钟限制**: 控制每分钟最大请求数
- **令牌桶算法**: 平滑处理突发请求

### 2. **智能重试机制**
- **速率限制重试**: 遇到 429 错误自动指数退避重试（最多10次）
- **网络错误重试**: 网络超时或连接错误自动重试（最多5次）
- **指数退避**: 重试间隔从1秒逐步增加到60秒

### 3. **请求控制**
- **请求间延迟**: 每次请求之间的最小延迟
- **并发控制**: 通过 `--concurrency` 参数控制同时进行的请求数

## ⚙️ 配置方式

### 方式一：命令行参数

```bash
python -m src.main --detect-only \
  --detect-dir output/batch_full_compact \
  --concurrency 5 \
  --api-key YOUR_API_KEY \
  --base-url YOUR_BASE_URL \
  --model YOUR_MODEL
```

### 方式二：环境变量

```bash
# 速率限制配置
export RATE_LIMIT_PER_MINUTE=60        # 每分钟最大请求数
export RATE_LIMIT_PER_SECOND=10        # 每秒最大请求数
export REQUEST_DELAY=0.1               # 请求间延迟（秒）

# 重试配置
export RATE_LIMIT_RETRY_ATTEMPTS=10    # 速率限制重试次数
export RETRY_ATTEMPTS=5                # 一般错误重试次数
export INITIAL_BACKOFF=1.0             # 初始退避时间（秒）
export MAX_BACKOFF=60.0                # 最大退避时间（秒）

# API 配置
export OPENAI_API_KEY=your-api-key
export OPENAI_BASE_URL=your-base-url
export OPENAI_MODEL=your-model
export API_TIMEOUT=120                 # API 超时时间（秒）

# 运行
python -m src.main --detect-only --detect-dir output/batch_full_compact
```

### 方式三：配置文件

参考 `config.rate_limit_examples.json` 中的示例配置。

## 📊 不同场景的推荐配置

### 场景 1: 小批量测试（1-50个合约）

```bash
export RATE_LIMIT_PER_MINUTE=60
export RATE_LIMIT_PER_SECOND=10
export REQUEST_DELAY=0.1

python -m src.main --detect-only \
  --detect-dir output/batch_full_compact \
  --concurrency 5 \
  --limit 50
```

**特点**: 快速、适合测试

### 场景 2: 中等批量（50-200个合约）

```bash
export RATE_LIMIT_PER_MINUTE=50
export RATE_LIMIT_PER_SECOND=8
export REQUEST_DELAY=0.15

python -m src.main --detect-only \
  --detect-dir output/batch_full_compact \
  --concurrency 10 \
  --limit 200
```

**特点**: 平衡速度和稳定性

### 场景 3: 大批量处理（200+个合约）

```bash
export RATE_LIMIT_PER_MINUTE=40
export RATE_LIMIT_PER_SECOND=5
export REQUEST_DELAY=0.2

python -m src.main --detect-only \
  --detect-dir output/batch_full_compact \
  --concurrency 20
```

**特点**: 稳定、适合长时间运行

### 场景 4: 超级安全模式（免费账户/测试）

```bash
export RATE_LIMIT_PER_MINUTE=15
export RATE_LIMIT_PER_SECOND=1
export REQUEST_DELAY=1.0

python -m src.main --detect-only \
  --detect-dir output/batch_full_compact \
  --concurrency 1 \
  --limit 10
```

**特点**: 极慢但绝对稳定

## 🔧 常见问题和解决方案

### 问题 1: 遇到 429 错误（Too Many Requests）

**症状**: 
```
⚠️  遇到速率限制，等待 2.0 秒后重试（第 1/10 次）
```

**解决方案**:
1. 降低速率限制：
   ```bash
   export RATE_LIMIT_PER_MINUTE=30  # 降低到原来的50%
   export RATE_LIMIT_PER_SECOND=3
   ```

2. 增加请求延迟：
   ```bash
   export REQUEST_DELAY=0.5  # 增加到0.5秒
   ```

3. 降低并发数：
   ```bash
   --concurrency 1  # 改为串行处理
   ```

4. 检查账户配额是否已用完

### 问题 2: 处理速度太慢

**症状**: 处理1000个合约需要几小时

**解决方案**:
1. 检查当前配置是否过于保守
2. 提高并发数（如果 API 允许）：
   ```bash
   --concurrency 20
   ```
3. 降低请求延迟：
   ```bash
   export REQUEST_DELAY=0.05
   ```
4. 考虑升级 API 账户等级

### 问题 3: 频繁超时

**症状**: 
```
⚠️  网络错误，等待 2.0 秒后重试: timeout
```

**解决方案**:
1. 增加超时时间：
   ```bash
   export API_TIMEOUT=180  # 增加到3分钟
   ```

2. 降低并发数：
   ```bash
   --concurrency 5
   ```

3. 检查网络连接质量

4. 使用更紧凑的输出模式（减少数据量）：
   ```bash
   python -m src.main --dataset data/dataset.json -m compact
   ```

## 📈 性能优化建议

### 1. **找到最优并发数**

从低并发开始，逐步增加：

```bash
# 测试 concurrency = 1
python -m src.main --detect-only --detect-dir output/batch_full_compact --concurrency 1 --limit 10

# 测试 concurrency = 5
python -m src.main --detect-only --detect-dir output/batch_full_compact --concurrency 5 --limit 10

# 测试 concurrency = 10
python -m src.main --detect-only --detect-dir output/batch_full_compact --concurrency 10 --limit 10
```

观察哪个配置速度最快且不出现错误。

### 2. **监控缓存命中率**

```
💾 缓存命中: 47 (94.0%)
```

高缓存命中率表示很多合约已经检测过，可以跳过 API 调用。

### 3. **分批处理大数据集**

对于1000+个合约，建议分批处理：

```bash
# 第一批: 0-200
python -m src.main --detect-only --detect-dir output/batch_full_compact --limit 200

# 第二批: 继续处理（缓存会跳过已处理的）
python -m src.main --detect-only --detect-dir output/batch_full_compact --limit 400

# 依此类推...
```

## 🎮 实际使用示例

### 示例 1: 使用阿里云通义千问（Qwen）

```bash
export RATE_LIMIT_PER_MINUTE=60
export RATE_LIMIT_PER_SECOND=10
export REQUEST_DELAY=0.1

python -m src.main --detect-only \
  --detect-dir output/batch_full_compact \
  --concurrency 8 \
  --api-key sk-your-qwen-key \
  --base-url https://dashscope.aliyuncs.com/compatible-mode/v1 \
  --model qwen-plus
```

### 示例 2: 使用 DeepSeek

```bash
export RATE_LIMIT_PER_MINUTE=50
export RATE_LIMIT_PER_SECOND=5
export REQUEST_DELAY=0.2

python -m src.main --detect-only \
  --detect-dir output/batch_full_compact \
  --concurrency 5 \
  --api-key sk-your-deepseek-key \
  --base-url https://api.deepseek.com/v1 \
  --model deepseek-chat
```

### 示例 3: 使用智谱 GLM-4

```bash
export RATE_LIMIT_PER_MINUTE=30
export RATE_LIMIT_PER_SECOND=3
export REQUEST_DELAY=0.3

python -m src.main --detect-only \
  --detect-dir output/batch_full_compact \
  --concurrency 3 \
  --api-key your-zhipu-key \
  --base-url https://open.bigmodel.cn/api/paas/v4 \
  --model glm-4
```

## 📊 速率限制原理说明

### 令牌桶算法

系统使用双层令牌桶：

1. **每秒令牌桶**: 
   - 初始令牌数 = `rate_limit_per_second`
   - 每秒补充 `rate_limit_per_second` 个令牌
   - 每次请求消耗 1 个令牌

2. **每分钟令牌桶**:
   - 初始令牌数 = `rate_limit_per_minute`
   - 每秒补充 `rate_limit_per_minute / 60` 个令牌
   - 每次请求消耗 1 个令牌

只有两个桶都有足够令牌时，请求才会被发送。

### 指数退避策略

遇到速率限制错误时：
- 第1次重试: 等待 1 秒
- 第2次重试: 等待 2 秒
- 第3次重试: 等待 4 秒
- 第4次重试: 等待 8 秒
- ...
- 最大等待: 60 秒

## 💡 最佳实践

1. **从保守配置开始**: 首次使用新的 API 提供商时，使用保守的速率限制
2. **逐步优化**: 观察实际表现，逐步提高并发和速率
3. **监控日志**: 关注警告和错误信息
4. **使用缓存**: 利用缓存机制避免重复请求
5. **分批处理**: 大数据集分批处理，便于中断和恢复
6. **错峰使用**: 在 API 使用低峰时段处理大批量任务

## 📞 获取帮助

如果遇到问题：
1. 查看 `config.rate_limit_examples.json` 中的配置示例
2. 检查 API 提供商的速率限制文档
3. 使用超级安全模式测试基本功能
4. 查看系统日志中的详细错误信息
