# Quick Reference Guide

## 🚀 One-Liner Commands

### Basic Analysis
```python
from src.analyzer import SolidityAnalyzer
analyzer = SolidityAnalyzer("0.4.x")
result = analyzer.analyze_file("contract.sol")
print(f"Success: {result['success']}, Nodes: {result['dfg_nodes']}")
```

### Batch Analysis
```python
result = analyzer.analyze_directory("contracts/")
print(f"Analyzed {result['successful_analyses']}/{result['total_files']} files")
```

### Source Code Analysis
```python
result = analyzer.analyze_source(source_code, "ContractName")
```

## 📊 Output Files

| File Type | Location | Content |
|-----------|----------|---------|
| DFG JSON | `output/dfgs/{Name}_dfg.json` | Complete graph structure |
| Summary | `output/dfgs/{Name}_summary.json` | Statistics overview |
| Graph | `output/graphs/{Name}_dfg.png` | Visual representation |
| Report | `output/analysis_report.json` | Batch analysis summary |

## 🔧 Common Patterns

### Error Handling
```python
if result["success"]:
    print(f"✅ {result['contract']}: {result['dfg_nodes']} nodes")
else:
    print(f"❌ Error: {result['error']}")
```

### Validation
```python
validation = analyzer.validate_setup()
if validation["components_ready"]:
    print("Ready to analyze!")
```

### Loading Results
```python
import json
with open(result['json_file'], 'r') as f:
    dfg_data = json.load(f)
```

## 🎯 Key Features

- **Solidity 0.4.x Support**: Legacy constructors, constant functions
- **Multiple Outputs**: JSON, PNG visualizations, summaries
- **Batch Processing**: Directory-level analysis
- **Error Recovery**: Graceful handling of parsing failures

## 🧪 Testing

```bash
python test_analyzer.py
```

Expected: `4/4 tests passing` 🎉

## 📋 Supported Node Types

- `contract_declaration`
- `function_definition` 
- `state_variable_declaration`
- `expression_statement`
- `binary_expression`
- `identifier`
- `number_literal`

## 🔗 Edge Types

- `control_dependency`: Control flow
- `definition`: Variable assignments
- `data_dependency`: Data flow

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| Tree-sitter error | `cd tree-sitter-solidity/bindings/python && pip install .` |
| Graphviz missing | `pip install graphviz` + system install |
| Import errors | Check Python path and `__init__.py` |

## 📈 Performance Tips

- Use caching for repeated analyses
- Process large contracts in batches
- Monitor memory usage for >100KB files
- Use parallel processing for multiple files

## 🎨 Visualization Colors

- **Blue edges**: Control dependencies
- **Green edges**: Data dependencies  
- **Red edges**: Definition relationships
- **Node shapes**: Different types (rectangles, ellipses, diamonds)

## 📞 Quick Help

```python
# Check what's available
print(dir(analyzer))
print(analyzer.validate_setup())
```

## 🔍 Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)
# Then run analysis
```

---

**Need more details?** See `USAGE_GUIDE.md` for comprehensive examples! 📚