"""
文件操作工具函数
提供各种文件格式的读写操作
"""

import pickle
import os
import json
from typing import Any, Dict, List

def read_txt(filepath: str) -> str:
    """
    读取文本文件
    
    Args:
        filepath: 文件路径
        
    Returns:
        str: 文件内容
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        text_content = f.read()
    return text_content

def save_txt(filepath: str, content: str) -> None:
    """
    保存文本文件
    
    Args:
        filepath: 文件路径
        content: 文件内容
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def read_pickle(filepath: str) -> Dict[str, Any]:
    """
    读取pickle文件
    
    Args:
        filepath: 文件路径
        
    Returns:
        Dict[str, Any]: 反序列化的数据
    """
    with open(filepath, 'rb') as f:
        data = pickle.load(f)
    return data

def save_pickle(filepath: str, data: Dict[str, Any]) -> None:
    """
    保存pickle文件
    
    Args:
        filepath: 文件路径
        data: 要序列化的数据
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'wb') as f:
        pickle.dump(data, f)

def read_md(filepath: str) -> str:
    """
    读取Markdown文件
    
    Args:
        filepath: 文件路径
        
    Returns:
        str: Markdown内容
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    return markdown_content

def save_md(filepath: str, content: str) -> None:
    """
    保存Markdown文件
    
    Args:
        filepath: 文件路径
        content: Markdown内容
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def read_json(filepath: str) -> Dict[str, Any]:
    """
    读取JSON文件
    
    Args:
        filepath: 文件路径
        
    Returns:
        Dict[str, Any]: JSON数据
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def save_json(filepath: str, data: Dict[str, Any]) -> None:
    """
    保存JSON文件
    
    Args:
        filepath: 文件路径
        data: JSON数据
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def ensure_dir(filepath: str) -> None:
    """
    确保目录存在
    
    Args:
        filepath: 文件路径
    """
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)

def file_exists(filepath: str) -> bool:
    """
    检查文件是否存在
    
    Args:
        filepath: 文件路径
        
    Returns:
        bool: 文件是否存在
    """
    return os.path.exists(filepath) and os.path.isfile(filepath)

def get_file_size(filepath: str) -> int:
    """
    获取文件大小
    
    Args:
        filepath: 文件路径
        
    Returns:
        int: 文件大小（字节）
    """
    if file_exists(filepath):
        return os.path.getsize(filepath)
    return 0
