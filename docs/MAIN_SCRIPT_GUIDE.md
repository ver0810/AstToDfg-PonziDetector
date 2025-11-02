# AST-Solidity 主调度脚本使用指南

## 概述

`src/main.py` 是 AST-Solidity 项目的主调度中心，提供完整的流水线功能：

**源代码 → AST → DFG → 检测 → 结果（可选可视化）**

## 快速开始

### 方式1：使用 Python 模块

```bash
# 分析单个合约
python -m src.main examples/solidity_04x/simple_contract.sol

# 分析并检测庞氏骗局
python -m src.main examples/solidity_04x/simple_contract.sol --detect

# 分析、检测并可视化
python -m src.main examples/solidity_04x/simple_contract.sol --detect --visualize
```

### 方式2：使用便捷脚本

```bash
# 首先给脚本添加执行权限
chmod +x ast-solidity.py

# 然后直接运行
./ast-solidity.py examples/solidity_04x/simple_contract.sol
```

### 方式3：使用 Python 直接调用

```bash
python ast-solidity.py examples/solidity_04x/simple_contract.sol --detect
```

## 命令行参数

### 基本参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `files` | Solidity源文件路径（支持多个） | 必需 |
| `-o, --output` | 输出目录 | `output` |
| `-v, --version` | Solidity版本 | `0.4.x` |

### DFG配置

| 参数 | 说明 | 可选值 | 默认值 |
|------|------|--------|--------|
| `-m, --mode` | DFG输出模式 | `compact`, `standard`, `verbose` | `standard` |

- **compact**: 紧凑模式，只保留关键节点
- **standard**: 标准模式，平衡详细度和可读性（推荐）
- **verbose**: 详细模式，保留所有节点

### 功能开关

| 参数 | 说明 |
|------|------|
| `-d, --detect` | 启用庞氏骗局检测 |
| `--visualize` | 启用DFG可视化（生成PNG图片） |
| `-b, --batch` | 批量处理模式 |

### LLM配置（用于检测）

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--api-key` | LLM API密钥 | 从环境变量 `OPENAI_API_KEY` 读取 |
| `--base-url` | LLM API基础URL | 从环境变量 `OPENAI_BASE_URL` 读取 |
| `--model` | LLM模型名称 | 从环境变量 `OPENAI_MODEL` 读取 |

## 使用示例

### 示例1：基本分析

分析单个合约，生成DFG：

```bash
python -m src.main examples/solidity_04x/simple_contract.sol
```

输出：
- `output/simple_contract.json` - DFG JSON文件

### 示例2：使用紧凑模式

生成更简洁的DFG（只包含关键节点）：

```bash
python -m src.main examples/solidity_04x/simple_contract.sol --mode compact
```

### 示例3：启用庞氏骗局检测

分析合约并检测是否为庞氏骗局：

```bash
python -m src.main examples/solidity_04x/simple_contract.sol --detect
```

输出：
- `output/simple_contract.json` - DFG JSON文件
- `output/simple_contract_detection.json` - 检测结果

### 示例4：完整流水线（分析+检测+可视化）

```bash
python -m src.main examples/solidity_04x/simple_contract.sol \
  --detect \
  --visualize \
  --mode standard \
  --output ./results
```

输出：
- `results/simple_contract.json` - DFG JSON文件
- `results/simple_contract_detection.json` - 检测结果
- `results/simple_contract_dfg.png` - DFG可视化图片

### 示例5：批量处理多个文件

```bash
python -m src.main \
  examples/solidity_04x/simple_contract.sol \
  examples/solidity_04x/DFS.sol \
  examples/solidity_04x/inheritance_example.sol \
  --batch \
  --detect \
  --output ./batch_results
```

输出：
- 每个合约的DFG JSON文件
- 每个合约的检测结果（如果启用）
- `batch_results/batch_result_YYYYMMDD_HHMMSS.json` - 批处理总结

### 示例6：指定Solidity版本

```bash
python -m src.main contract.sol --version 0.8.x
```

### 示例7：自定义LLM配置

```bash
python -m src.main contract.sol \
  --detect \
  --api-key "your-api-key" \
  --base-url "https://api.openai.com/v1" \
  --model "gpt-4"
```

## 流水线步骤说明

主调度脚本执行以下步骤：

```
[1/5] 读取源代码
     └─ 从文件读取Solidity源代码

[2/5] 构建AST
     └─ 使用tree-sitter解析源代码，生成抽象语法树

[3/5] 构建DFG
     └─ 从AST构建数据流图，保存为JSON

[4/5] 庞氏骗局检测（可选）
     └─ 使用LLM分析DFG，检测是否为庞氏骗局
     └─ 输出：是否为庞氏骗局、置信度、风险等级、推理过程

[5/5] 可视化（可选）
     └─ 生成DFG的Graphviz可视化图片
```

## 输出文件说明

### DFG JSON文件

包含完整的数据流图信息：

```json
{
  "contract": "ContractName",
  "solidity_version": "0.4.x",
  "nodes": {
    "node_id": {
      "id": "node_id",
      "type": "function",
      "name": "functionName",
      ...
    }
  },
  "edges": {
    "edge_id": {
      "from": "node_id_1",
      "to": "node_id_2",
      "type": "data_flow",
      ...
    }
  },
  "metadata": {
    "node_count": 10,
    "edge_count": 15,
    ...
  }
}
```

### 检测结果文件

包含庞氏骗局检测结果：

```json
{
  "contract_name": "ContractName",
  "classification_result": {
    "is_ponzi": false,
    "confidence": 0.85,
    "risk_level": "低",
    "reasoning": "该合约不包含典型的庞氏骗局特征..."
  },
  "code_hash": "md5_hash"
}
```

### 批处理结果文件

包含批量处理的总结：

```json
{
  "total_files": 3,
  "timestamp": "2025-11-02T10:30:00",
  "results": [...],
  "summary": {
    "success": 2,
    "failed": 1,
    "total_time": 45.6
  }
}
```

## 环境变量配置

如果需要使用检测功能，可以设置以下环境变量：

```bash
# Linux/Mac
export OPENAI_API_KEY="your-api-key"
export OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
export OPENAI_MODEL="qwen-plus"

# Windows (PowerShell)
$env:OPENAI_API_KEY="your-api-key"
$env:OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:OPENAI_MODEL="qwen-plus"
```

## Python API 使用

除了命令行，也可以在Python代码中直接使用：

```python
from src.main import SolidityPipeline
from src.dfg_builder.dfg_config import OutputMode
from pathlib import Path

# 创建流水线
pipeline = SolidityPipeline(
    solidity_version="0.4.x",
    output_dir="output",
    dfg_mode=OutputMode.STANDARD,
    enable_detection=True,
    enable_visualization=True
)

# 处理单个文件
result = pipeline.process_file(Path("contract.sol"))

# 批量处理
results = pipeline.process_batch([
    Path("contract1.sol"),
    Path("contract2.sol"),
    Path("contract3.sol")
])
```

## 常见问题

### Q: 如何查看帮助信息？

```bash
python -m src.main --help
```

### Q: 检测功能报错怎么办？

1. 确认已设置 LLM API 配置
2. 检查网络连接
3. 验证 API 密钥是否有效

### Q: 可视化功能需要什么依赖？

需要安装 Graphviz：

```bash
# Ubuntu/Debian
sudo apt-get install graphviz

# macOS
brew install graphviz

# Python包
pip install graphviz
```

### Q: 支持哪些Solidity版本？

目前主要支持 Solidity 0.4.x，其他版本正在开发中。

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

[项目许可证信息]
