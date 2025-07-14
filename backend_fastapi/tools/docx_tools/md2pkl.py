"""
Markdown转PKL工具
将Markdown文件转换为结构化的Pickle文件，提取论文的各个部分
"""

import re
import os
import pickle
from typing import Dict, List, Any, Tuple

def extract_abstracts(md_content: str) -> Tuple[str, str]:
    """
    提取中文和英文摘要
    
    Args:
        md_content: Markdown内容
        
    Returns:
        Tuple[str, str]: (中文摘要, 英文摘要)
    """
    zh_abs = ""
    en_abs = ""
    
    # 提取中文摘要
    zh_match = re.search(r'\*\*摘要\*\*(.*?)(?=\*\*关键词\*\*|\*\*ABSTRACT\*\*|\*\*KEY WORDS\*\*|$)', 
                        md_content, re.DOTALL)
    if zh_match:
        zh_abs = zh_match.group(1).strip()
    
    # 提取英文摘要
    en_match = re.search(r'\*\*ABSTRACT\*\*(.*?)(?=\*\*KEY WORDS\*\*|\*\*关键词\*\*|# 第|$)', 
                        md_content, re.DOTALL)
    if en_match:
        en_abs = en_match.group(1).strip()
    
    return zh_abs, en_abs

def extract_reference(md_content: str) -> str:
    """
    提取参考文献部分
    
    Args:
        md_content: Markdown内容
        
    Returns:
        str: 参考文献内容
    """
    ref_match = re.search(r'# 参考文献(.*?)(?=# 致谢|# 附录|\Z)', md_content, re.DOTALL)
    if ref_match:
        return ref_match.group(1).strip()
    return ""

def extract_chapters(md_content: str) -> List[Dict[str, Any]]:
    """
    提取章节内容
    
    Args:
        md_content: Markdown内容
        
    Returns:
        List[Dict[str, Any]]: 章节列表，每个章节包含名称、图片和内容
    """
    # 匹配所有章节
    chapter_pattern = r'(^# 第[一二三四五六七八九十]+章[\s\S]*?)(?=^# 第[一二三四五六七八九十]+章|^# 参考文献|^# 致谢|^# 附录|\Z)'
    chapter_matches = list(re.finditer(chapter_pattern, md_content, re.MULTILINE))
    
    chapters = []
    for match in chapter_matches:
        chapter_block = match.group(1)
        
        # 提取章节名
        chapter_name_match = re.match(r'^# (第[一二三四五六七八九十]+章[\s\S]*?)\n', chapter_block)
        chapter_name = chapter_name_match.group(1).strip() if chapter_name_match else ''
        
        # 提取图片路径
        images = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', chapter_block)
        
        # 提取正文内容（去掉章节名）
        content = chapter_block
        if chapter_name:
            content = content[len('# ' + chapter_name):].lstrip('\n')
        
        chapters.append({
            'chapter_name': chapter_name,
            'images': images,
            'content': content.strip()
        })
    
    return chapters

def convert_md_to_pkl(md_path: str, pkl_path: str) -> bool:
    """
    将Markdown文件转换为PKL格式
    
    Args:
        md_path: 输入的Markdown文件路径
        pkl_path: 输出的PKL文件路径
        
    Returns:
        bool: 转换是否成功
    """
    try:
        # 读取Markdown文件
        with open(md_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # 提取各部分内容
        zh_abs, en_abs = extract_abstracts(md_content)
        ref = extract_reference(md_content)
        chapters = extract_chapters(md_content)
        
        # 构建数据结构
        data = {
            'zh_abs': zh_abs,
            'en_abs': en_abs,
            'ref': ref,
            'chapters': chapters
        }
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(pkl_path), exist_ok=True)
        
        # 保存为PKL文件
        with open(pkl_path, 'wb') as f:
            pickle.dump(data, f)
        
        return True
        
    except Exception as e:
        print(f'转换失败: {str(e)}')
        return False

def convert_md_content_to_pkl_data(md_content: str) -> Dict[str, Any]:
    """
    将Markdown内容转换为PKL数据结构
    
    Args:
        md_content: Markdown内容字符串
        
    Returns:
        Dict[str, Any]: 结构化的数据
    """
    zh_abs, en_abs = extract_abstracts(md_content)
    ref = extract_reference(md_content)
    chapters = extract_chapters(md_content)
    
    return {
        'zh_abs': zh_abs,
        'en_abs': en_abs,
        'ref': ref,
        'chapters': chapters
    }
