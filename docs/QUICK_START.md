# 🚀 快速开始 - 新功能使用指南

本指南帮助您快速上手 AST-Solidity 2.0 的新功能。

## 📦 准备工作

### 1. 环境配置

```bash
# 设置 LLM API 密钥（可选）
export LLM_API_KEY="your-api-key"
export LLM_BASE_URL="https://api.example.com"
export LLM_MODEL="model-name"
```

### 2. 创建配置文件

```bash
# 复制示例配置
cp config.example.json config.json

# 编辑配置（添加您的 API 密钥）
vim config.json
```

## 🎯 使用场景

### 场景 1: 分析单个合约

**最简单的方式：**
```bash
python -m src.main contract.sol
```

**带检测和可视化：**
```bash
python -m src.main contract.sol --detect --visualize
```

**使用配置文件：**
```bash
python -m src.main contract.sol --config config.json
```

### 场景 2: 批量处理合约文件

**处理多个文件：**
```bash
python -m src.main contract1.sol contract2.sol contract3.sol --batch
```

**处理目录下所有合约：**
```bash
python -m src.main examples/solidity_04x/*.sol --batch
```

**批量 + 检测：**
```bash
python -m src.main *.sol --batch --detect --concurrency 20
```

### 场景 3: 处理数据集

**准备数据集文件** (`data.json`):
```json
[
  {
    "code": "contract MyContract { function test() public { } }",
    "label": 0
  },
  {
    "code": "contract PonziScheme { mapping(address => uint) public balances; }",
    "label": 1
  }
]
```

**处理数据集：**
```bash
# 处理整个数据集
python -m src.main --dataset data.json

# 限制处理数量（测试用）
python -m src.main --dataset data.json --limit 10

# 数据集 + 检测
python -m src.main --dataset data.json --detect

# 数据集 + 配置文件
python -m src.main --dataset data.json --config config.json
```

### 场景 4: 批量检测（已有 JSON 文件）

如果您已经生成了 DFG JSON 文件，可以只运行检测：

```bash
# 检测 output 目录的所有 JSON
python -m src.main --detect-only

# 自定义输入目录
python -m src.main --detect-only --detect-dir results

# 限制检测数量 + 自定义并发
python -m src.main --detect-only --limit 50 --concurrency 30

# 禁用缓存（强制重新检测）
python -m src.main --detect-only --no-cache
```

### 场景 5: 使用不同的 LLM 提供商

**Qwen (通义千问):**
```bash
python -m src.main contract.sol --detect \
  --llm-provider qwen \
  --api-key YOUR_QWEN_KEY \
  --model qwen-plus
```

**DeepSeek:**
```bash
python -m src.main contract.sol --detect \
  --llm-provider deepseek \
  --api-key YOUR_DEEPSEEK_KEY \
  --model deepseek-chat
```

**OpenAI:**
```bash
python -m src.main contract.sol --detect \
  --llm-provider openai \
  --api-key YOUR_OPENAI_KEY \
  --model gpt-4
```

## 🔧 配置文件详解

### 基本配置 (`config.json`)

```json
{
  "solidity_version": "0.4.x",
  "dfg": {
    "mode": "standard"
  },
  "detection": {
    "enabled": false,
    "concurrency_limit": 40,
    "cache_enabled": true,
    "provider": {
      "name": "qwen",
      "api_key": null,
      "base_url": null,
      "model": null
    }
  },
  "output": {
    "output_dir": "output"
  }
}
```

### 配置项说明

| 配置项 | 说明 | 可选值 |
|--------|------|--------|
| `solidity_version` | Solidity 版本 | `0.4.x`, `0.5.x`, `0.6.x`, `0.7.x`, `0.8.x` |
| `dfg.mode` | DFG 输出模式 | `compact`, `standard`, `verbose` |
| `detection.enabled` | 是否启用检测 | `true`, `false` |
| `detection.concurrency_limit` | 并发数 | `1-100` (推荐 20-40) |
| `detection.cache_enabled` | 是否启用缓存 | `true`, `false` |
| `detection.provider.name` | LLM 提供商 | `qwen`, `deepseek`, `openai` |
| `output.output_dir` | 输出目录 | 任意路径 |

## 📊 输出文件说明

### DFG JSON 输出

位置: `output/` 目录

格式示例:
```json
{
  "contract_name": "MyContract",
  "dfg": {
    "nodes": [...],
    "edges": [...]
  },
  "statistics": {
    "total_nodes": 100,
    "total_edges": 150
  },
  "label": 0,
  "metadata": {...}
}
```

### 检测结果输出

位置: `results/` 目录

文件:
- `detection_results_TIMESTAMP.json` - 完整结果
- `detection_summary_TIMESTAMP.json` - 统计摘要

### 批量处理输出

- `batch_result_TIMESTAMP.json` - 批量文件处理结果
- `dataset_result_TIMESTAMP.json` - 数据集处理结果

## 🎓 完整工作流示例

### 示例 1: 研究型项目

```bash
# 步骤 1: 分析单个合约，生成可视化
python -m src.main test.sol --visualize --verbose

# 步骤 2: 如果需要检测
python -m src.main test.sol --detect --visualize

# 步骤 3: 查看结果
ls output/  # DFG JSON 和 PNG
ls results/  # 检测结果
```

### 示例 2: 大规模数据集处理

```bash
# 步骤 1: 配置 LLM
cat > config.json << EOF
{
  "detection": {
    "enabled": true,
    "concurrency_limit": 30,
    "provider": {
      "name": "qwen",
      "api_key": "YOUR_KEY"
    }
  }
}
EOF

# 步骤 2: 小批量测试
python -m src.main --dataset data.json --limit 10 --config config.json

# 步骤 3: 全量处理
python -m src.main --dataset data.json --config config.json

# 步骤 4: 查看结果统计
cat results/detection_summary_*.json
```

### 示例 3: 两阶段处理（推荐大规模数据集）

```bash
# 阶段 1: 只生成 DFG（不检测）
python -m src.main --dataset data.json

# 阶段 2: 批量检测已生成的 JSON
python -m src.main --detect-only --concurrency 40

# 好处:
# - 可以多次检测，不用重新生成 DFG
# - 缓存机制节省 API 调用
# - 可以暂停/恢复
```

## 🔍 常见问题

### Q1: 如何查看缓存命中率？

A: 使用 `--detect-only` 模式时会自动显示：

```
💾 缓存命中: 45 (75.0%)
```

### Q2: 如何清空缓存？

A: 删除 cache 目录或使用 `--no-cache`:

```bash
rm -rf cache/
# 或
python -m src.main --detect-only --no-cache
```

### Q3: 并发数设置多少合适？

A: 根据 API 限制:
- Qwen: 20-40
- DeepSeek: 20-30
- OpenAI: 10-20

### Q4: 数据集格式有什么要求？

A: 必须包含 `code` 字段，其他字段可选:

```json
[
  {
    "code": "contract { }",  // 必须
    "label": 0,              // 可选
    "name": "Contract1"      // 可选
  }
]
```

### Q5: 如何批量处理但不检测？

A: 不加 `--detect` 参数即可：

```bash
python -m src.main --dataset data.json
```

### Q6: 检测失败怎么办？

A: 查看错误信息：

```bash
# 详细输出
python -m src.main --detect-only --verbose

# 查看错误详情
cat results/detection_results_*.json | jq '.errors'
```

## 💡 性能优化建议

### 1. 使用缓存

```bash
# 启用缓存（默认）
python -m src.main --detect-only

# 第二次运行会很快（缓存命中）
python -m src.main --detect-only
```

### 2. 合理设置并发

```bash
# 根据 API 限制调整
python -m src.main --detect-only --concurrency 30
```

### 3. 分批处理大数据集

```bash
# 每次处理 100 个
python -m src.main --dataset data.json --limit 100
```

### 4. 两阶段处理

```bash
# 先生成 DFG（快速，本地）
python -m src.main --dataset data.json

# 再批量检测（慢，API调用）
python -m src.main --detect-only
```

## 🎯 推荐工作流

### 新手推荐

```bash
# 1. 从单个文件开始
python -m src.main test.sol --visualize

# 2. 尝试检测
python -m src.main test.sol --detect

# 3. 批量处理小数据集
python -m src.main --dataset small_data.json --limit 10
```

### 专业用户推荐

```bash
# 1. 创建配置文件
cp config.example.json config.json
vim config.json

# 2. 两阶段处理大数据集
python -m src.main --dataset data.json --config config.json  # DFG生成
python -m src.main --detect-only --config config.json        # 批量检测

# 3. 分析结果
python analyze_results.py results/detection_summary_*.json
```

---

**需要帮助？** 

查看完整文档:
- `docs/UPGRADE_GUIDE.md` - 详细功能说明
- `docs/MAIN_SCRIPT_GUIDE.md` - 主脚本完整指南
- `config.example.json` - 配置文件示例

**遇到问题？**

1. 检查配置文件格式
2. 验证 API 密钥
3. 查看详细输出 (`--verbose`)
4. 检查错误日志
