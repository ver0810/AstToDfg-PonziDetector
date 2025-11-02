#!/usr/bin/env python3
"""
AST-Solidity 主调度脚本快速演示
展示如何使用主调度脚本处理Solidity合约
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """运行命令并显示输出"""
    print(f"\n{'='*70}")
    print(f"示例: {description}")
    print(f"{'='*70}")
    print(f"命令: {cmd}")
    print(f"{'='*70}\n")
    
    result = subprocess.run(cmd, shell=True, capture_output=False, text=True)
    return result.returncode == 0

def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                  AST-Solidity 主调度脚本演示                          ║
║                                                                      ║
║  功能: 源代码 → AST → DFG → 检测 → 结果（可选可视化）                 ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    # 检查示例文件是否存在
    example_file = Path("examples/solidity_04x/simple_contract.sol")
    if not example_file.exists():
        print(f"❌ 示例文件不存在: {example_file}")
        print("   请确保在项目根目录运行此脚本")
        return 1
    
    print("\n提示: 以下是一些常用命令示例，您可以根据需要选择运行\n")
    
    examples = [
        {
            "description": "查看帮助信息",
            "command": "python -m src.main --help",
            "run": False  # 设置为True自动运行
        },
        {
            "description": "基本分析 - 生成DFG",
            "command": f"python -m src.main {example_file}",
            "run": False
        },
        {
            "description": "使用紧凑模式",
            "command": f"python -m src.main {example_file} --mode compact",
            "run": False
        },
        {
            "description": "启用庞氏骗局检测",
            "command": f"python -m src.main {example_file} --detect",
            "run": False
        },
        {
            "description": "完整流水线（分析+检测+可视化）",
            "command": f"python -m src.main {example_file} --detect --visualize",
            "run": False
        },
        {
            "description": "批量处理多个文件",
            "command": "python -m src.main examples/solidity_04x/*.sol --batch",
            "run": False
        },
    ]
    
    # 显示所有示例
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['description']}")
        print(f"   命令: {example['command']}")
    
    print(f"\n{'='*70}")
    print("运行示例")
    print(f"{'='*70}\n")
    
    # 可以选择自动运行某些示例
    for example in examples:
        if example.get('run', False):
            run_command(example['command'], example['description'])
    
    print(f"\n{'='*70}")
    print("手动运行示例")
    print(f"{'='*70}\n")
    print("您可以复制上面的命令并在终端中运行它们。\n")
    print("推荐的第一步:")
    print(f"  python -m src.main {example_file}\n")
    print("如果需要检测功能，请先配置环境变量:")
    print("  export OPENAI_API_KEY='your-api-key'")
    print("  export OPENAI_BASE_URL='your-api-url'")
    print("  export OPENAI_MODEL='your-model'\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
