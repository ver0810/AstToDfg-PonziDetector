#!/bin/bash
# 批量处理完整的庞氏合约数据集 - 紧凑模式

echo "🚀 开始批量处理 Ponzi 合约数据集 (紧凑模式)"
echo "================================================"
echo ""

# 配置
INPUT_FILE="data/ponzi_code_dataset_small_1514.json"
OUTPUT_DIR="output/ponzi_dfgs_compact"
MODE="compact"
PROGRESS=100

# 检查输入文件
if [ ! -f "$INPUT_FILE" ]; then
    echo "❌ 错误: 输入文件不存在: $INPUT_FILE"
    exit 1
fi

# 创建输出目录
mkdir -p "$OUTPUT_DIR"

# 显示配置
echo "📋 处理配置:"
echo "  输入文件: $INPUT_FILE"
echo "  输出目录: $OUTPUT_DIR"
echo "  模式:     $MODE (最小节点)"
echo "  进度间隔: 每 $PROGRESS 个合约"
echo ""

# 显示数据集信息
total_contracts=$(wc -l < "$INPUT_FILE")
file_size=$(du -h "$INPUT_FILE" | cut -f1)
echo "📊 数据集信息:"
echo "  总合约数: $total_contracts"
echo "  文件大小: $file_size"
echo ""

# 预估时间
estimated_time=$((total_contracts / 35))  # compact模式更快
echo "⏱️  预估时间: 约 $estimated_time 秒 ($(echo "scale=1; $estimated_time/60" | bc) 分钟)"
echo ""

# 开始处理
echo "🏃 开始处理..."
echo "================================================"
echo ""

python batch_process.py \
    "$INPUT_FILE" \
    "$OUTPUT_DIR" \
    --mode "$MODE" \
    --progress "$PROGRESS"

# 检查结果
if [ $? -eq 0 ]; then
    echo ""
    echo "================================================"
    echo "✅ 处理完成!"
    echo ""
    echo "📁 输出文件:"
    echo "  目录: $OUTPUT_DIR"
    echo "  文件数: $(ls -1 "$OUTPUT_DIR"/*.json 2>/dev/null | wc -l)"
    echo "  总大小: $(du -sh "$OUTPUT_DIR" | cut -f1)"
    echo ""
    
    # 显示示例文件
    echo "📝 示例文件:"
    ls -1 "$OUTPUT_DIR"/*.json 2>/dev/null | head -5
    echo ""
    
    # 检查错误日志
    if [ -f "$OUTPUT_DIR/errors.log" ]; then
        error_count=$(grep -c "^行号" "$OUTPUT_DIR/errors.log" || echo "0")
        if [ "$error_count" -gt 0 ]; then
            echo "⚠️  警告: 发现 $error_count 个处理错误"
            echo "  查看详情: $OUTPUT_DIR/errors.log"
        fi
    fi
else
    echo ""
    echo "❌ 处理失败!"
    exit 1
fi
