import json
import os

def add_labels_to_output():
    """
    将数据集中的label字段添加到输出目录的JSON文件中
    """
    
    # 数据集文件路径
    dataset_file = "data/ponzi_code_dataset_small_1514.json"
    
    # 输出目录路径
    output_dir = "output/batch_full_compact"
    
    print(f"开始处理数据集: {dataset_file}")
    print(f"输出目录: {output_dir}")
    
    # 读取数据集
    try:
        with open(dataset_file, 'r', encoding='utf-8') as f:
            dataset_lines = f.readlines()
        print(f"成功读取数据集，共 {len(dataset_lines)} 行")
    except Exception as e:
        print(f"读取数据集失败: {e}")
        return
    
    # 解析数据集，提取label信息
    labels = {}
    for i, line in enumerate(dataset_lines):
        line = line.strip()
        if line:
            try:
                data = json.loads(line)
                if 'label' in data:
                    labels[i] = data['label']
            except json.JSONDecodeError as e:
                print(f"解析第 {i} 行失败: {e}")
                continue
    
    print(f"成功提取 {len(labels)} 个label")
    
    # 处理输出目录中的所有JSON文件
    if not os.path.exists(output_dir):
        print(f"输出目录不存在: {output_dir}")
        return
    
    output_files = [f for f in os.listdir(output_dir) if f.endswith('.json')]
    print(f"找到 {len(output_files)} 个输出文件")
    
    updated_count = 0
    error_count = 0
    
    for filename in output_files:
        filepath = os.path.join(output_dir, filename)
        
        try:
            # 读取输出文件
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取index信息
            if 'metadata' in data and 'index' in data['metadata']:
                index = data['metadata']['index']
                
                # 如果有对应的label，则更新
                if index in labels:
                    old_label = data.get('label', 'N/A')
                    data['label'] = labels[index]
                    
                    # 写回文件
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    
                    updated_count += 1
                    print(f"更新文件 {filename}: index {index}, label {old_label} -> {labels[index]}")
                else:
                    print(f"文件 {filename}: index {index} 在数据集中无对应label")
            else:
                print(f"文件 {filename}: 缺少metadata或index字段")
                
        except Exception as e:
            error_count += 1
            print(f"处理文件 {filename} 时出错: {e}")
    
    print(f"\n处理完成:")
    print(f"  - 成功更新: {updated_count} 个文件")
    print(f"  - 错误: {error_count} 个文件")
    print(f"  - 总计: {len(output_files)} 个文件")

if __name__ == "__main__":
    add_labels_to_output()
