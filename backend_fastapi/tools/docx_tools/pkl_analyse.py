"""
PKL文件分析工具
分析和处理pickle格式的论文数据
"""

import pickle
import os
from typing import Dict, List, Any, Optional

def load_pkl_file(pkl_path: str) -> Dict[str, Any]:
    """
    加载PKL文件
    
    Args:
        pkl_path: PKL文件路径
        
    Returns:
        Dict[str, Any]: 加载的数据
    """
    with open(pkl_path, 'rb') as f:
        data = pickle.load(f)
    return data

def analyze_pkl_structure(pkl_path: str) -> Dict[str, Any]:
    """
    分析PKL文件结构
    
    Args:
        pkl_path: PKL文件路径
        
    Returns:
        Dict[str, Any]: 分析结果
    """
    try:
        data = load_pkl_file(pkl_path)
        
        analysis = {
            'file_path': pkl_path,
            'file_size': os.path.getsize(pkl_path),
            'has_zh_abs': bool(data.get('zh_abs', '')),
            'has_en_abs': bool(data.get('en_abs', '')),
            'has_ref': bool(data.get('ref', '')),
            'chapter_count': len(data.get('chapters', [])),
            'chapters': []
        }
        
        # 分析章节信息
        for i, chapter in enumerate(data.get('chapters', [])):
            chapter_info = {
                'index': i,
                'name': chapter.get('chapter_name', ''),
                'content_length': len(chapter.get('content', '')),
                'image_count': len(chapter.get('images', [])),
                'images': chapter.get('images', [])
            }
            analysis['chapters'].append(chapter_info)
        
        return analysis
        
    except Exception as e:
        return {
            'error': str(e),
            'file_path': pkl_path
        }

def get_chapter_content(pkl_path: str, chapter_index: int) -> Optional[Dict[str, Any]]:
    """
    获取指定章节的内容
    
    Args:
        pkl_path: PKL文件路径
        chapter_index: 章节索引
        
    Returns:
        Optional[Dict[str, Any]]: 章节内容，如果不存在则返回None
    """
    try:
        data = load_pkl_file(pkl_path)
        chapters = data.get('chapters', [])
        
        if 0 <= chapter_index < len(chapters):
            return chapters[chapter_index]
        
        return None
        
    except Exception:
        return None

def extract_all_images(pkl_path: str) -> List[str]:
    """
    提取所有章节中的图片路径
    
    Args:
        pkl_path: PKL文件路径
        
    Returns:
        List[str]: 所有图片路径列表
    """
    try:
        data = load_pkl_file(pkl_path)
        all_images = []
        
        for chapter in data.get('chapters', []):
            all_images.extend(chapter.get('images', []))
        
        return all_images
        
    except Exception:
        return []

def get_document_summary(pkl_path: str) -> Dict[str, Any]:
    """
    获取文档摘要信息
    
    Args:
        pkl_path: PKL文件路径
        
    Returns:
        Dict[str, Any]: 文档摘要
    """
    try:
        data = load_pkl_file(pkl_path)
        
        total_content_length = sum(
            len(chapter.get('content', '')) 
            for chapter in data.get('chapters', [])
        )
        
        total_images = sum(
            len(chapter.get('images', [])) 
            for chapter in data.get('chapters', [])
        )
        
        return {
            'zh_abstract_length': len(data.get('zh_abs', '')),
            'en_abstract_length': len(data.get('en_abs', '')),
            'reference_length': len(data.get('ref', '')),
            'chapter_count': len(data.get('chapters', [])),
            'total_content_length': total_content_length,
            'total_images': total_images,
            'chapters': [
                {
                    'name': chapter.get('chapter_name', ''),
                    'content_length': len(chapter.get('content', '')),
                    'image_count': len(chapter.get('images', []))
                }
                for chapter in data.get('chapters', [])
            ]
        }
        
    except Exception as e:
        return {'error': str(e)}
