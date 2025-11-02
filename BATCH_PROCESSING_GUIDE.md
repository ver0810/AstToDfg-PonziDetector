# 批量处理指南

本指南说明如何使用 `batch_process.py` 批量处理Solidity合约数据集并生成DFG。

## 功能特点

- ✅ 批量处理JSONL格式的Solidity合约数据集
- ✅ 支持三种输出模式：compact（精简）/ standard（标准）/ verbose（详细）
- ✅ 不生成可视化文件,仅生成DFG JSON
- ✅ 自动过滤和优化节点,减少70-85%的冗余节点
- ✅ 实时进度显示和性能统计
- ✅ 错误日志记录
- ✅ 保存完整元数据(源行号、标签、模式等)

## 输入格式

输入文件应为JSONL格式(每行一个JSON对象):

```json
{"code": "pragma solidity ^0.4.0;\ncontract Example {...}", "label": 0}
{"code": "pragma solidity ^0.4.18;\ncontract Test {...}", "label": 1}
```

每个JSON对象包含:
- `code`: Solidity源代码(字符串)
- `label`: 分类标签(整数,如0=正常, 1=庞氏骗局等)

## 使用方法

### 基本用法

```bash
# 使用标准模式处理
python batch_process.py data/ponzi_code_dataset_small_1514.json output/batch_dfgs
```

### 指定输出模式

```bash
# 精简模式 (节点最少,约87%减少率)
python batch_process.py data/contracts.json output/dfgs_compact --mode compact

# 标准模式 (平衡,约81%减少率,推荐)
python batch_process.py data/contracts.json output/dfgs_standard --mode standard

# 详细模式 (保留所有节点)
python batch_process.py data/contracts.json output/dfgs_verbose --mode verbose
```

### 自定义进度显示

```bash
# 每50个合约显示一次进度
python batch_process.py data/contracts.json output/dfgs --progress 50

# 每处理1个合约就显示进度(适合小数据集)
python batch_process.py data/small.json output/dfgs --progress 1
```

## 输出结果

### 输出文件命名

每个合约生成一个DFG JSON文件:

```
output/batch_dfgs/
├── line1_ContractName_dfg.json      # 第1行的合约
├── line2_AnotherContract_dfg.json   # 第2行的合约
├── line100_TokenSale_dfg.json       # 第100行的合约
└── errors.log                       # 错误日志(如果有)
```

文件名格式: `line{行号}_{合约名}_dfg.json`

### DFG JSON结构

```json
{
  "contract": "ContractName",
  "solidity_version": "0.4.x",
  "nodes": {
    "dfg_node_1": {
      "id": "dfg_node_1",
      "type": "contract",
      "name": "ContractName",
      "scope": "global",
      "source_location": {...}
    }
  },
  "edges": {
    "dfg_edge_1": {
      "id": "dfg_edge_1",
      "source": "dfg_node_1",
      "target": "dfg_node_2",
      "type": "definition"
    }
  },
  "metadata": {
    "source_line": 1,
    "label": 0,
    "mode": "standard",
    "contract_name": "ContractName"
  }
}
```

### 统计信息

处理完成后会显示:

```
============================================================
📈 批量处理完成!
============================================================
总合约数:     1514
成功处理:     1498 (99%)
处理失败:     16
跳过:         0
总耗时:       30.5 秒
平均速率:     49.64 contracts/s

🎯 节点优化统计:
优化前节点总数: 1094357
优化后节点总数: 209130
节点减少率:     80.9%

📁 输出目录: output/batch_dfgs
============================================================
```

## 性能参考

基于测试数据:

| 模式     | 节点减少率 | 处理速度 | 适用场景 |
|---------|----------|---------|---------|
| compact | ~87%     | 最快    | 仅需核心信息 |
| standard| ~81%     | 中等    | 推荐默认使用 |
| verbose | 0%       | 较慢    | 需要完整信息 |

实测处理速度: ~50 contracts/s (取决于合约复杂度)

## 三种模式对比

### Compact 模式
- **节点保留**: 仅核心节点(合约、函数、状态变量等)
- **减少率**: ~87%
- **适用**: 机器学习特征提取、快速分析
- **示例**: SimpleStorage合约 47节点 → 6节点

### Standard 模式 (推荐)
- **节点保留**: 核心+重要节点
- **减少率**: ~81%
- **适用**: 大多数分析场景
- **示例**: SimpleStorage合约 47节点 → 9节点

### Verbose 模式
- **节点保留**: 所有节点
- **减少率**: 0%
- **适用**: 需要完整AST信息
- **示例**: SimpleStorage合约 47节点 → 47节点

## 错误处理

如果有合约处理失败,会:
1. 跳过该合约继续处理下一个
2. 在 `errors.log` 中记录错误信息
3. 最终统计中显示失败数量

错误日志示例:
```
批量处理错误日志
============================================================
总错误数: 2

行号 156: Failed to build AST
行号 892: Failed to build DFG
```

## 完整示例

### 示例1: 处理庞氏合约数据集

```bash
# 创建输出目录
mkdir -p output/ponzi_dfgs

# 使用标准模式批量处理
python batch_process.py \
  data/ponzi_code_dataset_small_1514.json \
  output/ponzi_dfgs \
  --mode standard \
  --progress 100

# 查看结果
ls -lh output/ponzi_dfgs/ | head
cat output/ponzi_dfgs/line1_ResetPonzi_dfg.json | jq '.metadata'
```

### 示例2: 小数据集测试

```bash
# 创建测试数据(前10个合约)
head -10 data/ponzi_code_dataset_small_1514.json > data/test_10.json

# 使用紧凑模式快速测试
python batch_process.py \
  data/test_10.json \
  output/test_compact \
  --mode compact \
  --progress 5

# 查看优化效果
cat output/test_compact/line1_*.json | jq '.nodes | length'
```

### 示例3: 详细模式保留完整信息

```bash
# 使用详细模式(不过滤节点)
python batch_process.py \
  data/important_contracts.json \
  output/full_dfgs \
  --mode verbose
```

## 常见问题

### Q: 处理很慢怎么办?
A: 
1. 使用 `--mode compact` 加快速度
2. 检查是否有特别大的合约拖慢速度
3. 分批处理大数据集

### Q: 某些合约处理失败?
A: 
1. 查看 `errors.log` 了解具体原因
2. 可能是Solidity语法不支持或代码不完整
3. 失败的合约会自动跳过,不影响其他合约

### Q: 如何提取特定信息?
A: 使用 `jq` 工具提取JSON字段:
```bash
# 提取所有合约的节点数
jq '.nodes | length' output/batch_dfgs/*.json

# 提取标签为1的合约
jq 'select(.metadata.label == 1)' output/batch_dfgs/*.json

# 统计各类节点数量
jq '.nodes | group_by(.type) | map({type: .[0].type, count: length})' line1_*.json
```

### Q: 内存不足怎么办?
A: 分批处理大数据集:
```bash
# 分批处理
split -l 500 data/large_dataset.json data/batch_
for batch in data/batch_*; do
  python batch_process.py $batch output/batch_$(basename $batch)
done
```

## 下一步

处理完DFG后,可以:

1. **特征提取**: 从DFG中提取图特征用于机器学习
2. **模式分析**: 分析控制流和数据流模式
3. **漏洞检测**: 基于DFG模式检测潜在漏洞
4. **相似度分析**: 比较不同合约的DFG结构
5. **可视化**: 使用Graphviz等工具可视化特定合约的DFG

## 相关文档

- [OPTIMIZATION_GUIDE.md](OPTIMIZATION_GUIDE.md) - DFG优化详细说明
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 快速参考
- [README.md](README.md) - 项目总览
