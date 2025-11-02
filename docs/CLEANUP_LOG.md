# 项目清理说明

## 清理时间
2025-11-02

## 删除的文件

### 已废弃的脚本
以下脚本已被新的主调度脚本 `src/main.py` 替代：

- ✅ `batch_process.py` - 旧的批量处理脚本
- ✅ `run_batch_compact.sh` - Shell批处理脚本（紧凑模式）
- ✅ `run_batch_standard.sh` - Shell批处理脚本（标准模式）
- ✅ `run_test.py` - 旧的测试脚本
- ✅ `example_optimization.py` - 优化示例（已有文档）
- ✅ `example_usage.py` - 使用示例（已有文档）

### 临时测试文件
- ✅ `test_imports.py` - 导入测试
- ✅ `test_main.py` - 主脚本测试

### 特定工具脚本
- ✅ `add_labels_to_output.py` - 数据标注工具

### 旧文档
- ✅ `BATCH_PROCESSING_GUIDE.md` - 已被 `docs/MAIN_SCRIPT_GUIDE.md` 替代

### 临时输出目录
- ✅ `batch_test/`
- ✅ `batch_results/`
- ✅ `test_output/`
- ✅ `test_output2/`
- ✅ `output_test/`
- ✅ `results/`

## 保留的文件

### 主要脚本
- `ast-solidity.py` - 命令行入口脚本
- `demo_main.py` - 演示脚本

### 文档
- `README.md` - 主文档
- `docs/` - 完整文档目录
  - `MAIN_SCRIPT_GUIDE.md` - 主脚本使用指南
  - `OPTIMIZATION_GUIDE.md` - DFG优化指南
  - `USAGE_GUIDE.md` - 详细使用指南
  - `QUICK_REFERENCE.md` - 快速参考
  - 其他文档...

### 核心代码
- `src/` - 源代码目录
  - `main.py` - 主调度脚本 ⭐
  - `analyzer.py` - 分析器
  - `ast_builder/` - AST构建模块
  - `dfg_builder/` - DFG构建模块
  - `visualization/` - 可视化模块
  - `detector/` - 检测模块
  - `utils/` - 工具模块

### 测试
- `test/` - 单元测试目录
  - `test_analyzer.py`
  - `test_config.py`
  - `add_actual_labels.py`

### 数据和示例
- `data/` - 测试数据
- `examples/` - 示例合约
- `tree-sitter-solidity/` - Solidity解析器

## 新的项目结构

```
ast-solidity/
├── ast-solidity.py          # 🚀 CLI入口
├── demo_main.py             # 📋 演示脚本
├── README.md                # 📖 主文档
├── requirements.txt         # 📦 依赖
│
├── src/                     # 核心代码
│   ├── main.py             # ⭐ 主调度脚本
│   ├── analyzer.py
│   ├── json_serializer.py
│   ├── ast_builder/
│   ├── dfg_builder/
│   ├── visualization/
│   ├── detector/
│   └── utils/
│
├── docs/                    # 文档
│   ├── MAIN_SCRIPT_GUIDE.md
│   ├── OPTIMIZATION_GUIDE.md
│   ├── USAGE_GUIDE.md
│   └── ...
│
├── test/                    # 测试
├── examples/                # 示例
├── data/                    # 数据
├── output/                  # 输出
└── tree-sitter-solidity/    # 解析器

```

## 使用新的工作流

### 替代旧脚本的命令

**旧方式:**
```bash
python batch_process.py input.json output_dir
bash run_batch_compact.sh
python example_optimization.py
```

**新方式:**
```bash
# 单文件分析
python -m src.main contract.sol

# 批量处理（紧凑模式）
python -m src.main *.sol --batch --mode compact

# 完整流水线
python -m src.main contract.sol --detect --visualize

# 查看演示
python demo_main.py
```

## 优势

1. **统一入口** - 所有功能通过一个脚本访问
2. **更清晰** - 减少根目录文件数量
3. **更灵活** - 通过参数配置，而不是多个脚本
4. **更易维护** - 集中管理功能
5. **更好的文档** - 完整的使用指南

## 迁移指南

如果您之前使用旧脚本，请参考：
- [主脚本使用指南](docs/MAIN_SCRIPT_GUIDE.md)
- [快速参考](docs/QUICK_REFERENCE.md)
