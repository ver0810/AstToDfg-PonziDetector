#!/usr/bin/env python3
"""
Example usage script for Solidity AST to DFG construction system
Demonstrates basic functionality and common usage patterns
"""

import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    print("🚀 Solidity AST to DFG Construction System - Example Usage")
    print("=" * 60)
    
    # Import the analyzer
    try:
        from src.analyzer import SolidityAnalyzer
        print("✅ Successfully imported SolidityAnalyzer")
    except ImportError as e:
        print(f"❌ Failed to import: {e}")
        print("Make sure all dependencies are installed:")
        print("  pip install -r requirements.txt")
        print("  cd tree-sitter-solidity/bindings/python && pip install .")
        return 1
    
    # Initialize analyzer
    print("\n🔧 Initializing analyzer for Solidity 0.4.x...")
    analyzer = SolidityAnalyzer(solidity_version="0.4.x")
    
    # Validate setup
    validation = analyzer.validate_setup()
    print(f"📋 Setup validation:")
    for component, status in validation.items():
        icon = "✅" if status else "❌"
        print(f"  {icon} {component}: {status}")
    
    if not validation["components_ready"]:
        print("\n❌ Some components are not ready. Please check the setup.")
        return 1
    
    # Example 1: Analyze source code directly
    print("\n📝 Example 1: Analyzing source code directly")
    print("-" * 40)
    
    simple_contract = """
pragma solidity 0.4.24;

contract SimpleContract {
    uint256 public value;
    
    function SimpleContract() public {
        value = 42;
    }
    
    function setValue(uint256 _value) public {
        value = _value;
    }
    
    function getValue() public constant returns (uint256) {
        return value;
    }
}
"""
    
    result = analyzer.analyze_source(simple_contract, "SimpleContract")
    
    if result["success"]:
        print(f"✅ Analysis successful!")
        print(f"   Contract: {result['contract']}")
        print(f"   Version: {result['solidity_version']}")
        print(f"   AST Nodes: {result['ast_nodes']}")
        print(f"   DFG Nodes: {result['dfg_nodes']}")
        print(f"   DFG Edges: {result['dfg_edges']}")
        print(f"   Output files:")
        print(f"     - JSON: {result['json_file']}")
        print(f"     - Graph: {result['visualization_file']}")
    else:
        print(f"❌ Analysis failed: {result['error']}")
    
    # Example 2: Analyze example files
    print("\n📁 Example 2: Analyzing example files")
    print("-" * 40)
    
    examples_dir = Path("examples/solidity_04x")
    if examples_dir.exists():
        result = analyzer.analyze_directory(str(examples_dir))
        
        print(f"📊 Directory analysis results:")
        print(f"   Total files: {result['total_files']}")
        print(f"   Successful: {result['successful_analyses']}")
        print(f"   Failed: {result['failed_analyses']}")
        print(f"   Success rate: {result['successful_analyses']/result['total_files']*100:.1f}%")
        
        # Show details for each contract
        print(f"\n📋 Contract details:")
        detailed_results = result.get('detailed_results', result.get('results', []))
        for contract_result in detailed_results:
            if contract_result['success']:
                print(f"   ✅ {contract_result['contract']}: {contract_result['dfg_nodes']} nodes, {contract_result['dfg_edges']} edges")
            else:
                print(f"   ❌ {contract_result.get('contract', 'Unknown')}: {contract_result.get('error', 'Unknown error')}")
    else:
        print(f"⚠️  Example directory not found: {examples_dir}")
    
    # Example 3: Load and examine results
    print("\n🔍 Example 3: Examining generated results")
    print("-" * 40)
    
    # Try to load a summary file
    summary_file = Path("output/dfgs/SimpleContract_summary.json")
    if summary_file.exists():
        import json
        with open(summary_file, 'r') as f:
            summary = json.load(f)
        
        print(f"📈 Contract summary for {summary['contract']}:")
        print(f"   Total nodes: {summary['statistics']['total_nodes']}")
        print(f"   Total edges: {summary['statistics']['total_edges']}")
        print(f"   Functions: {len(summary['functions'])}")
        for func in summary['functions']:
            print(f"     - {func['name']} (scope: {func['scope']})")
        print(f"   State variables: {len(summary['state_variables'])}")
        for var in summary['state_variables']:
            print(f"     - {var['name']}: {var['data_type']}")
    else:
        print(f"⚠️  Summary file not found: {summary_file}")
    
    # Example 4: Show available outputs
    print("\n📂 Example 4: Generated output files")
    print("-" * 40)
    
    output_dir = Path("output")
    if output_dir.exists():
        print(f"📁 Output directory structure:")
        
        for subdir in ["dfgs", "graphs"]:
            subdir_path = output_dir / subdir
            if subdir_path.exists():
                files = list(subdir_path.glob("*"))
                print(f"   {subdir}/: {len(files)} files")
                for file in sorted(files)[:3]:  # Show first 3 files
                    size = file.stat().st_size
                    print(f"     - {file.name} ({size} bytes)")
                if len(files) > 3:
                    print(f"     ... and {len(files) - 3} more files")
    else:
        print(f"⚠️  Output directory not found: {output_dir}")
    
    print("\n🎉 Example script completed!")
    print("\n💡 Next steps:")
    print("   1. Check the generated files in 'output/' directory")
    print("   2. Open the PNG graphs to see visualizations")
    print("   3. Examine JSON files for detailed DFG data")
    print("   4. Try analyzing your own Solidity contracts")
    print("   5. Read USAGE_GUIDE.md for advanced examples")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())