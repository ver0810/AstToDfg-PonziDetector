# Usage Guide - Solidity AST to DFG Construction System

This guide provides detailed examples and best practices for using the Solidity AST to DFG construction system.

## 📚 Table of Contents

1. [Basic Usage](#basic-usage)
2. [Working with Different Input Types](#working-with-different-input-types)
3. [Understanding Outputs](#understanding-outputs)
4. [Advanced Configuration](#advanced-configuration)
5. [Real-World Examples](#real-world-examples)
6. [Performance Tips](#performance-tips)
7. [Error Handling](#error-handling)

## 🚀 Basic Usage

### 1. Simple Contract Analysis

```python
from src.analyzer import SolidityAnalyzer

# Initialize analyzer for Solidity 0.4.x
analyzer = SolidityAnalyzer(solidity_version="0.4.x")

# Analyze a contract file
result = analyzer.analyze_file("examples/solidity_04x/simple_contract.sol")

# Check results
if result["success"]:
    print(f"✅ Contract analyzed successfully!")
    print(f"📊 AST Nodes: {result['ast_nodes']}")
    print(f"🔗 DFG Nodes: {result['dfg_nodes']}")
    print(f"📈 DFG Edges: {result['dfg_edges']}")
    print(f"📁 Output files:")
    print(f"  - JSON: {result['json_file']}")
    print(f"  - Visualization: {result['visualization_file']}")
else:
    print(f"❌ Analysis failed: {result['error']}")
```

### 2. Quick Source Code Analysis

```python
# Analyze source code directly
source_code = """
pragma solidity 0.4.24;

contract SimpleContract {
    uint256 public value;
    
    function SimpleContract() public {
        value = 100;
    }
    
    function setValue(uint256 _value) public {
        value = _value;
    }
    
    function getValue() public constant returns (uint256) {
        return value;
    }
}
"""

result = analyzer.analyze_source(source_code, "SimpleContract")
print(f"Analysis complete: {result['success']}")
```

## 📁 Working with Different Input Types

### 1. Single File Analysis

```python
# Analyze a specific contract file
file_path = "path/to/your/contract.sol"
result = analyzer.analyze_file(file_path)

# Extract detailed information
if result["success"]:
    print(f"Contract Name: {result['contract']}")
    print(f"Solidity Version: {result['solidity_version']}")
    print(f"Generated Files:")
    print(f"  - DFG JSON: {result['json_file']}")
    print(f"  - Summary: {result['summary_file']}")
    print(f"  - Graph: {result['visualization_file']}")
```

### 2. Directory Batch Analysis

```python
# Analyze all Solidity files in a directory
directory_path = "contracts/"
result = analyzer.analyze_directory(directory_path)

print(f"📊 Batch Analysis Results:")
print(f"  Total files: {result['total_files']}")
print(f"  Successful: {result['successful_analyses']}")
print(f"  Failed: {result['failed_analyses']}")
print(f"  Success Rate: {result['successful_analyses']/result['total_files']*100:.1f}%")

# Access detailed results for each contract
for contract_result in result['detailed_results']:
    if contract_result['success']:
        print(f"✅ {contract_result['contract']}: {contract_result['dfg_nodes']} nodes")
    else:
        print(f"❌ {contract_result['contract']}: {contract_result['error']}")
```

### 3. Multiple Contract Files

```python
import glob

# Analyze multiple specific files
contract_files = glob.glob("contracts/*.sol")
results = []

for file_path in contract_files:
    result = analyzer.analyze_file(file_path)
    results.append(result)
    
    if result["success"]:
        print(f"✅ Analyzed {result['contract']}")
    else:
        print(f"❌ Failed to analyze {file_path}: {result['error']}")

# Generate summary statistics
successful = sum(1 for r in results if r["success"])
total_nodes = sum(r["dfg_nodes"] for r in results if r["success"])
total_edges = sum(r["dfg_edges"] for r in results if r["success"])

print(f"\n📈 Summary:")
print(f"  Successful analyses: {successful}/{len(results)}")
print(f"  Total DFG nodes: {total_nodes}")
print(f"  Total DFG edges: {total_edges}")
```

## 📊 Understanding Outputs

### 1. DFG JSON Structure

The main DFG file contains complete graph information:

```python
import json

# Load and examine DFG structure
with open("output/dfgs/ContractName_dfg.json", "r") as f:
    dfg_data = json.load(f)

print(f"Contract: {dfg_data['contract']}")
print(f"Version: {dfg_data['solidity_version']}")
print(f"Total Nodes: {len(dfg_data['nodes'])}")
print(f"Total Edges: {len(dfg_data['edges'])}")

# Examine node types
node_types = {}
for node_id, node_data in dfg_data['nodes'].items():
    node_type = node_data['type']
    node_types[node_type] = node_types.get(node_type, 0) + 1

print("Node Types Distribution:")
for node_type, count in sorted(node_types.items()):
    print(f"  {node_type}: {count}")

# Examine edge types
edge_types = {}
for edge_id, edge_data in dfg_data['edges'].items():
    edge_type = edge_data['type']
    edge_types[edge_type] = edge_types.get(edge_type, 0) + 1

print("Edge Types Distribution:")
for edge_type, count in sorted(edge_types.items()):
    print(f"  {edge_type}: {count}")
```

### 2. Summary Statistics

```python
# Load summary report
with open("output/dfgs/ContractName_summary.json", "r") as f:
    summary = json.load(f)

print(f"📊 Contract Statistics:")
print(f"  Functions: {len(summary['functions'])}")
for func in summary['functions']:
    print(f"    - {func['name']} (scope: {func['scope']})")

print(f"  State Variables: {len(summary['state_variables'])}")
for var in summary['state_variables']:
    print(f"    - {var['name']}: {var['data_type']} (scope: {var['scope']})")
```

### 3. Analysis Report

```python
# Load comprehensive analysis report
with open("output/analysis_report.json", "r") as f:
    report = json.load(f)

print(f"📈 Analysis Summary:")
print(f"  Success Rate: {report['analysis_summary']['success_rate']*100:.1f}%")
print(f"  Total Contracts: {report['statistics']['total_contracts']}")
print(f"  Average Nodes/Contract: {report['statistics']['average_nodes_per_contract']:.1f}")
print(f"  Average Edges/Contract: {report['statistics']['average_edges_per_contract']:.1f}")
```

## ⚙️ Advanced Configuration

### 1. Custom Output Directory

```python
# Use custom output directory
analyzer = SolidityAnalyzer(
    solidity_version="0.4.x",
    output_directory="custom_analysis_output"
)

# The analyzer will create the directory if it doesn't exist
result = analyzer.analyze_file("contract.sol")
print(f"Files saved to: {result['json_file']}")
```

### 2. Component-Level Access

```python
from src.ast_builder import ASTBuilder
from src.dfg_builder import DFGBuilder
from src.solidity_04x_handler import Solidity04xHandler

# Build AST only
ast_builder = ASTBuilder()
ast_root = ast_builder.build_ast(source_code)

if ast_root:
    print(f"AST built successfully with {len(ast_root.children)} top-level nodes")
    
    # Process 0.4.x specific features
    handler = Solidity04xHandler()
    processed_ast = handler.process_legacy_constructors(ast_root)
    
    # Build DFG
    dfg_builder = DFGBuilder()
    dfg = dfg_builder.build_dfg(processed_ast)
    
    print(f"DFG built with {len(dfg.nodes)} nodes and {len(dfg.edges)} edges")
```

### 3. Validation and Setup

```python
# Validate analyzer setup before use
validation = analyzer.validate_setup()

print("Setup Validation:")
for component, status in validation.items():
    status_icon = "✅" if status else "❌"
    print(f"  {status_icon} {component}: {status}")

if validation["components_ready"]:
    print("🎉 Analyzer is ready for use!")
else:
    print("⚠️  Some components are not properly initialized")
```

## 🌍 Real-World Examples

### 1. Analyzing a Token Contract

```python
# Example: ERC20-like token contract
token_contract = """
pragma solidity 0.4.24;

contract SimpleToken {
    string public name;
    string public symbol;
    uint8 public decimals;
    uint256 public totalSupply;
    
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    
    function SimpleToken(uint256 initialSupply) public {
        totalSupply = initialSupply;
        balanceOf[msg.sender] = initialSupply;
        name = "SimpleToken";
        symbol = "STK";
        decimals = 18;
    }
    
    function transfer(address to, uint256 value) public returns (bool success) {
        require(balanceOf[msg.sender] >= value);
        balanceOf[msg.sender] -= value;
        balanceOf[to] += value;
        return true;
    }
    
    function approve(address spender, uint256 value) public returns (bool success) {
        allowance[msg.sender][spender] = value;
        return true;
    }
    
    function transferFrom(address from, address to, uint256 value) public returns (bool success) {
        require(value <= balanceOf[from]);
        require(value <= allowance[from][msg.sender]);
        balanceOf[from] -= value;
        balanceOf[to] += value;
        allowance[from][msg.sender] -= value;
        return true;
    }
}
"""

result = analyzer.analyze_source(token_contract, "SimpleToken")

if result["success"]:
    print(f"✅ Token contract analyzed!")
    print(f"📊 Complexity: {result['dfg_nodes']} nodes, {result['dfg_edges']} edges")
    
    # Load summary for detailed insights
    import json
    with open(result['summary_file'], 'r') as f:
        summary = json.load(f)
    
    print(f"🔍 Functions found: {len(summary['functions'])}")
    print(f"💾 State variables: {len(summary['state_variables'])}")
```

### 2. Analyzing Inheritance Hierarchies

```python
# Example: Contract with inheritance
inheritance_contract = """
pragma solidity 0.4.24;

contract Base {
    uint256 public baseValue;
    
    function Base() public {
        baseValue = 100;
    }
    
    function baseFunction() public constant returns (uint256) {
        return baseValue;
    }
}

contract Child is Base {
    uint256 public childValue;
    
    function Child() public {
        childValue = 200;
    }
    
    function childFunction() public constant returns (uint256) {
        return childValue + baseValue;
    }
}
"""

result = analyzer.analyze_source(inheritance_contract, "Child")

if result["success"]:
    print(f"✅ Inheritance contract analyzed!")
    
    # Check for inheritance relationships in the DFG
    with open(result['json_file'], 'r') as f:
        dfg_data = json.load(f)
    
    # Look for contract nodes
    contracts = [node for node in dfg_data['nodes'].values() 
                if node['type'] == 'contract']
    
    print(f"📋 Contracts found: {len(contracts)}")
    for contract in contracts:
        print(f"  - {contract['text']}")
```

### 3. Batch Analysis of Project

```python
import os
from pathlib import Path

def analyze_project(project_path):
    """Analyze all Solidity files in a project"""
    analyzer = SolidityAnalyzer(solidity_version="0.4.x")
    
    # Find all .sol files
    sol_files = list(Path(project_path).rglob("*.sol"))
    
    print(f"🔍 Found {len(sol_files)} Solidity files")
    
    results = []
    for sol_file in sol_files:
        try:
            result = analyzer.analyze_file(str(sol_file))
            results.append(result)
            
            if result["success"]:
                print(f"✅ {sol_file.name}: {result['dfg_nodes']} nodes")
            else:
                print(f"❌ {sol_file.name}: {result['error']}")
                
        except Exception as e:
            print(f"💥 {sol_file.name}: Exception - {e}")
    
    # Generate project summary
    successful = [r for r in results if r["success"]]
    
    if successful:
        total_nodes = sum(r["dfg_nodes"] for r in successful)
        total_edges = sum(r["dfg_edges"] for r in successful)
        
        print(f"\n📊 Project Summary:")
        print(f"  Analyzed: {len(successful)}/{len(sol_files)} files")
        print(f"  Total DFG nodes: {total_nodes}")
        print(f"  Total DFG edges: {total_edges}")
        print(f"  Average complexity: {total_nodes/len(successful):.1f} nodes/contract")

# Usage
# analyze_project("my-solidity-project/")
```

## ⚡ Performance Tips

### 1. Memory Management

```python
# For large contracts, process in batches
def analyze_large_contract(source_code, contract_name):
    analyzer = SolidityAnalyzer(solidity_version="0.4.x")
    
    # Analyze in chunks if needed
    if len(source_code) > 100000:  # 100KB threshold
        print("⚠️  Large contract detected, consider splitting analysis")
    
    result = analyzer.analyze_source(source_code, contract_name)
    
    # Clear memory if needed
    import gc
    gc.collect()
    
    return result
```

### 2. Parallel Processing

```python
from concurrent.futures import ThreadPoolExecutor
import multiprocessing

def analyze_files_parallel(file_paths, max_workers=None):
    """Analyze multiple files in parallel"""
    if max_workers is None:
        max_workers = min(4, multiprocessing.cpu_count())
    
    def analyze_single(file_path):
        analyzer = SolidityAnalyzer(solidity_version="0.4.x")
        return analyzer.analyze_file(file_path)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(analyze_single, file_paths))
    
    return results

# Usage
# file_paths = ["contract1.sol", "contract2.sol", "contract3.sol"]
# results = analyze_files_parallel(file_paths)
```

### 3. Caching Results

```python
import hashlib
import json
from pathlib import Path

def analyze_with_cache(source_code, contract_name, cache_dir="analysis_cache"):
    """Analyze with caching to avoid reprocessing"""
    # Create cache directory
    Path(cache_dir).mkdir(exist_ok=True)
    
    # Generate cache key
    content_hash = hashlib.md5(source_code.encode()).hexdigest()
    cache_file = Path(cache_dir) / f"{contract_name}_{content_hash}.json"
    
    # Check cache
    if cache_file.exists():
        print(f"📋 Loading from cache: {contract_name}")
        with open(cache_file, 'r') as f:
            return json.load(f)
    
    # Analyze and cache result
    print(f"🔍 Analyzing: {contract_name}")
    analyzer = SolidityAnalyzer(solidity_version="0.4.x")
    result = analyzer.analyze_source(source_code, contract_name)
    
    # Save to cache
    with open(cache_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    return result
```

## 🚨 Error Handling

### 1. Common Error Scenarios

```python
def safe_analyze(analyzer, file_path):
    """Analyze with comprehensive error handling"""
    try:
        # Check if file exists
        if not Path(file_path).exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        # Check file size
        file_size = Path(file_path).stat().st_size
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            return {"success": False, "error": f"File too large: {file_size} bytes"}
        
        # Attempt analysis
        result = analyzer.analyze_file(file_path)
        
        # Validate result
        if not isinstance(result, dict):
            return {"success": False, "error": "Invalid result format"}
        
        if "success" not in result:
            result["success"] = False
            result["error"] = "Success flag missing"
        
        return result
        
    except MemoryError:
        return {"success": False, "error": "Memory error - file too large"}
    except Exception as e:
        return {"success": False, "error": f"Unexpected error: {str(e)}"}
```

### 2. Validation Functions

```python
def validate_analysis_result(result):
    """Validate analysis result structure"""
    required_fields = ["success", "contract"]
    optional_fields = ["ast_nodes", "dfg_nodes", "dfg_edges", "error"]
    
    # Check required fields
    for field in required_fields:
        if field not in result:
            return False, f"Missing required field: {field}"
    
    # If successful, check analysis-specific fields
    if result["success"]:
        analysis_fields = ["ast_nodes", "dfg_nodes", "dfg_edges"]
        for field in analysis_fields:
            if field not in result:
                return False, f"Missing analysis field: {field}"
            
            if not isinstance(result[field], int) or result[field] < 0:
                return False, f"Invalid value for {field}: {result[field]}"
    
    return True, "Valid result"

# Usage
result = analyzer.analyze_file("contract.sol")
is_valid, message = validate_analysis_result(result)
if not is_valid:
    print(f"❌ Invalid result: {message}")
```

### 3. Logging and Debugging

```python
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('analysis.log'),
        logging.StreamHandler()
    ]
)

def analyze_with_logging(analyzer, file_path):
    """Analyze with detailed logging"""
    logging.info(f"Starting analysis of {file_path}")
    
    try:
        result = analyzer.analyze_file(file_path)
        
        if result["success"]:
            logging.info(f"✅ Successfully analyzed {result['contract']}")
            logging.info(f"   AST nodes: {result['ast_nodes']}")
            logging.info(f"   DFG nodes: {result['dfg_nodes']}")
            logging.info(f"   DFG edges: {result['dfg_edges']}")
        else:
            logging.error(f"❌ Analysis failed: {result['error']}")
        
        return result
        
    except Exception as e:
        logging.error(f"💥 Exception during analysis: {e}", exc_info=True)
        return {"success": False, "error": f"Exception: {str(e)}"}
```

## 📝 Best Practices

1. **Always validate results** before using them
2. **Use caching** for repeated analyses of the same contracts
3. **Monitor memory usage** when analyzing large contracts
4. **Handle errors gracefully** and provide meaningful error messages
5. **Use logging** for debugging and monitoring
6. **Batch process** multiple files for better performance
7. **Validate input files** before analysis (existence, size, format)

This comprehensive usage guide should help you get the most out of the Solidity AST to DFG construction system! 🚀