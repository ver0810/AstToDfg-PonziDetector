# Solidity AST to DFG Construction System

A comprehensive system for parsing Solidity smart contracts (specifically targeting 0.4.x versions) and constructing Abstract Syntax Trees (AST) and Data Flow Graphs (DFG) for static analysis and security auditing.

## 🚀 Features

- **Solidity 0.4.x Support**: Specialized handling for legacy Solidity features
- **AST Construction**: Complete Abstract Syntax Tree generation using tree-sitter
- **DFG Generation**: Data Flow Graph construction with control, data, and definition dependencies
- **Multiple Output Formats**: JSON exports, PNG visualizations, and summary reports
- **Batch Processing**: Analyze individual files or entire directories
- **Legacy Feature Support**: Handles constructors, constant keywords, and 0.4.x syntax

## 📋 Requirements

- Python 3.8+
- tree-sitter
- tree-sitter-solidity
- graphviz (for visualization)
- NetworkX (for graph operations)

## 🛠️ Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd ast-solidity
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Install tree-sitter-solidity**:
```bash
cd tree-sitter-solidity/bindings/python
pip install .
```

4. **Install Graphviz** (system dependency):
```bash
# Ubuntu/Debian
sudo apt-get install graphviz

# macOS
brew install graphviz

# Windows
# Download and install from https://graphviz.org/download/
```

## 📁 Project Structure

```
ast-solidity/
├── src/                           # Core modules
│   ├── analyzer.py               # Main orchestrator
│   ├── ast_builder.py             # AST construction
│   ├── dfg_builder.py             # DFG construction
│   ├── solidity_04x_handler.py    # 0.4.x specific handling
│   ├── json_serializer.py         # JSON export
│   ├── visualizer.py              # Graph visualization
│   └── node_types.py              # Type definitions
├── examples/solidity_04x/         # Example contracts
├── output/                        # Generated outputs
│   ├── dfgs/                      # JSON DFG files
│   └── graphs/                    # PNG visualizations
├── tree-sitter-solidity/          # Parser library
└── test_analyzer.py               # Test suite
```

## 🎯 Quick Start

### Basic Usage

```python
from src.analyzer import SolidityAnalyzer

# Create analyzer for Solidity 0.4.x
analyzer = SolidityAnalyzer(solidity_version="0.4.x")

# Analyze a single file
result = analyzer.analyze_file("path/to/contract.sol")

print(f"Contract: {result['contract']}")
print(f"AST Nodes: {result['ast_nodes']}")
print(f"DFG Nodes: {result['dfg_nodes']}")
print(f"Success: {result['success']}")
```

### Analyze Source Code Directly

```python
# Analyze Solidity source code string
source_code = """
pragma solidity 0.4.24;

contract Test {
    uint256 public value;
    
    function Test() public {
        value = 0;
    }
    
    function setValue(uint256 _value) public {
        value = _value;
    }
}
"""

result = analyzer.analyze_source(source_code, "TestContract")
```

### Batch Analysis

```python
# Analyze entire directory
result = analyzer.analyze_directory("contracts/")

print(f"Total files: {result['total_files']}")
print(f"Successful: {result['successful_analyses']}")
print(f"Failed: {result['failed_analyses']}")
```

## 📊 Output Formats

### 1. JSON DFG Files
Location: `output/dfs/{ContractName}_dfg.json`

Contains complete DFG structure with:
- Node definitions with types, scopes, and metadata
- Edge relationships (control, data, definition dependencies)
- Source location information
- Solidity version-specific metadata

### 2. Summary Reports
Location: `output/dfgs/{ContractName}_summary.json`

Provides high-level statistics:
- Node and edge counts by type
- Function and state variable listings
- Contract-level metrics

### 3. Graph Visualizations
Location: `output/graphs/{ContractName}_dfg.png`

Visual representation of the DFG showing:
- Control flow (blue edges)
- Data dependencies (green edges)
- Definition relationships (red edges)
- Node types with different colors and shapes

### 4. Analysis Reports
Location: `output/analysis_report.json`

Comprehensive report for batch analysis including:
- Success rates and statistics
- Per-contract analysis results
- Aggregate metrics

## 🔧 Advanced Usage

### Custom Configuration

```python
# Create analyzer with custom output directory
analyzer = SolidityAnalyzer(
    solidity_version="0.4.x",
    output_directory="custom_output"
)

# Validate setup before analysis
validation = analyzer.validate_setup()
if validation["components_ready"]:
    print("Analyzer ready for use")
else:
    print("Setup incomplete")
```

### Working with Specific Components

```python
from src.ast_builder import ASTBuilder
from src.dfg_builder import DFGBuilder
from src.solidity_04x_handler import Solidity04xHandler

# Build AST only
ast_builder = ASTBuilder()
ast_root = ast_builder.build_ast(source_code)

# Handle 0.4.x specific features
handler = Solidity04xHandler()
processed_ast = handler.process_legacy_constructors(ast_root)

# Build DFG from AST
dfg_builder = DFGBuilder()
dfg = dfg_builder.build_dfg(processed_ast)
```

## 🧪 Testing

Run the complete test suite:

```bash
python test_analyzer.py
```

The test suite includes:
- Basic functionality tests
- Simple contract analysis
- File analysis
- Directory batch processing

Expected output:
```
开始测试Solidity AST到DFG构建系统
==================================================
=== 测试基本功能 ===
✅ 基本功能测试通过
=== 测试简单合约分析 ===
✅ 简单合约分析测试通过
=== 测试文件分析 ===
✅ 文件分析测试通过
=== 测试目录分析 ===
✅ 目录分析测试通过
==================================================
测试结果: 4/4 通过
🎉 所有测试通过！
```

## 📝 Supported Solidity 0.4.x Features

### Legacy Constructors
```solidity
contract MyContract {
    function MyContract() public {
        // Constructor logic
    }
}
```

### Constant Functions
```solidity
function getValue() public constant returns (uint256) {
    return value;
}
```

### Type Syntax
```solidity
uint256 public value;
address public owner;
bool public isActive;
```

### Visibility Modifiers
- `public`
- `private` 
- `internal`
- `external`

### State Mutability
- `constant` (0.4.x equivalent of `view`)
- `payable`

## 🔍 Node Types

The system recognizes and processes various AST node types:

### Contract-Level
- `contract_declaration`
- `inheritance_specifier`
- `state_variable_declaration`

### Function-Level  
- `function_definition`
- `constructor_definition`
- `parameter_list`
- `return_type_definition`

### Statements
- `expression_statement`
- `return_statement`
- `if_statement`
- `for_statement`
- `while_statement`

### Expressions
- `binary_expression`
- `unary_expression`
- `assignment_expression`
- `call_expression`
- `member_expression`
- `identifier`
- `number_literal`

## 🔗 Edge Types

The DFG includes three types of edges:

1. **Control Dependency** (`control_dependency`): Control flow relationships
2. **Definition** (`definition`): Variable definitions and assignments
3. **Data Dependency** (`data_dependency`): Data flow between variables

## 📈 Example Output

### Analysis Result
```json
{
  "contract": "SimpleStorage",
  "solidity_version": "0.4.x",
  "success": true,
  "ast_nodes": 36,
  "dfg_nodes": 47,
  "dfg_edges": 46,
  "json_file": "output/dfgs/SimpleStorage_dfg.json",
  "summary_file": "output/dfgs/SimpleStorage_summary.json",
  "visualization_file": "output/graphs/SimpleStorage_dfg.png"
}
```

### Summary Statistics
```json
{
  "statistics": {
    "total_nodes": 47,
    "total_edges": 46,
    "entry_node": null
  },
  "node_types": {
    "identifier": 34,
    "contract": 1,
    "state_variable": 1,
    "constructor_function": 1,
    "function": 2
  },
  "edge_types": {
    "control_dependency": 33,
    "definition": 7,
    "data_dependency": 6
  }
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Tree-sitter Language Loading Error**
   ```
   Warning: Failed to initialize tree-sitter language
   ```
   **Solution**: Ensure tree-sitter-solidity is properly installed:
   ```bash
   cd tree-sitter-solidity/bindings/python
   pip install .
   ```

2. **Graphviz Import Error**
   ```
   ImportError: No module named 'graphviz'
   ```
   **Solution**: Install both Python package and system binary:
   ```bash
   pip install graphviz
   sudo apt-get install graphviz  # Linux
   ```

3. **Visualization Warnings**
   ```
   Warning: using box for unknown shape doubleellipse
   ```
   **Solution**: These are non-critical warnings. The visualization will still be generated.

### Debug Mode

Enable verbose output for debugging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

analyzer = SolidityAnalyzer(solidity_version="0.4.x")
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔮 Future Enhancements

- Support for newer Solidity versions (0.5.x, 0.6.x, 0.7.x, 0.8.x)
- Additional analysis metrics
- Interactive web-based visualization
- Integration with security analysis tools
- Performance optimizations for large contracts
- Support for Yul intermediate representation

## 📞 Support

For issues, questions, or contributions:
- Create an issue on GitHub
- Check the test suite for usage examples
- Review the example contracts in `examples/solidity_04x/`