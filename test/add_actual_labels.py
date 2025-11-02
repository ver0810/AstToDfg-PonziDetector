import json
import os
from pathlib import Path


def proccess_func(data):
  
  data['label'] = 1
  return data
  
  
def process_json_files(directory, process_func):
    """
    批量处理目录下的所有JSON文件
    
    Args:
        directory: 目录路径
        process_func: 处理函数，接收json数据，返回处理后的数据
    """
    directory = Path(directory)
    processed_count = 0
    error_count = 0
    
    # 遍历目录下的所有文件
    for file_path in directory.rglob('*.json'):  # rglob递归查找子目录
        try:
            print(f"处理文件: {file_path}")
            
            # 读取JSON文件
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 处理数据
            processed_data = process_func(data)
            
            # 写回文件
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
            processed_count += 1
            
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")
            error_count += 1
    
    print(f"处理完成: 成功 {processed_count} 个文件，失败 {error_count} 个文件")
    return processed_count, error_count
