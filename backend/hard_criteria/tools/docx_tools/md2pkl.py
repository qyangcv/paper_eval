#!/usr/bin/env python3
"""
Markdown转PKL工具
将Markdown文件转换为结构化的Pickle文件，提取论文的各个部分

功能特性：
- 自动提取中文和英文摘要
- 提取参考文献部分
- 按章节分割内容
- 提取图片路径信息
- 保存为结构化的PKL格式

支持的文档结构：
- 摘要部分：**摘要** 和 **ABSTRACT**
- 关键词部分：**关键词** 和 **KEY WORDS**
- 章节部分：# 第一章、# 第二章等
- 参考文献：# 参考文献
- 图片：![...](图片路径)

依赖要求：
    Python标准库（re, os, pickle, argparse）

使用方法：
    python md2pkl.py <markdown文件路径> [选项]
    
命令行参数：
    md_file             输入的Markdown文件路径（必需）
    -o, --output        输出的PKL文件路径（可选，默认为输入文件名.pkl）

使用示例：
    # 基本用法（输出文件自动命名）
    python md2pkl.py document.md
    
    # 指定输出文件
    python md2pkl.py document.md -o output.pkl
    
    # 作为模块导入使用
    from md2pkl import convert_md_to_pkl
    convert_md_to_pkl("input.md", "output.pkl")

输出格式：
    PKL文件包含以下字段：
    - zh_abs: 中文摘要
    - en_abs: 英文摘要  
    - ref: 参考文献
    - chapters: 章节列表，每个章节包含：
      - chapter_name: 章节名称
      - images: 图片路径列表
      - content: 章节内容

注意事项：
- 确保输入文件为UTF-8编码的Markdown文件
- 章节标题必须使用标准格式（# 第一章、# 第二章等）
- 摘要和关键词部分需要使用**粗体**格式
- 输出目录会自动创建（如果不存在）

"""

import re
import os
import pickle
import argparse

def read_md(path):
    """
    读取Markdown文件内容
    
    Args:
        path (str): Markdown文件路径
        
    Returns:
        str: 文件内容
    """
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_abstracts(md):
    """
    提取中文和英文摘要
    
    Args:
        md (str): Markdown文本内容
        
    Returns:
        tuple: (中文摘要, 英文摘要)
    """
    # 中文摘要
    zh_abs = ''
    en_abs = ''
    zh_match = re.search(r'\*\*摘要\*\*\n([\s\S]*?)\n\*\*关键词', md)
    if zh_match:
        zh_abs = zh_match.group(1).strip()
    # 英文摘要
    en_match = re.search(r'\*\*ABSTRACT\*\*\n([\s\S]*?)\n\*\*KEY WORDS', md)
    if en_match:
        en_abs = en_match.group(1).strip()
    return zh_abs, en_abs

def extract_reference(md):
    """
    提取参考文献部分
    
    Args:
        md (str): Markdown文本内容
        
    Returns:
        str: 参考文献内容
    """
    ref = ''
    ref_match = re.search(r'# 参考文献\n([\s\S]*?)(?=\n# |\Z)', md)
    if ref_match:
        ref = ref_match.group(1).strip()
    return ref

def extract_chapters(md):
    """
    提取章节内容
    
    Args:
        md (str): Markdown文本内容
        
    Returns:
        list: 章节列表，每个章节包含名称、图片和内容
    """
    # 匹配所有章节（# 第一章 ... # 第二章 ... # 第三章 ...）
    # 章节标题格式：# 第一章 ...\n
    # 找到所有章节标题的位置
    chapter_iter = list(re.finditer(r'(^# 第[一二三四五六七八九十]+章[\s\S]*?)(?=^# 第[一二三四五六七八九十]+章|^# 参考文献|^# 致谢|^# 附录|\Z)', md, re.MULTILINE))
    chapters = []
    for m in chapter_iter:
        chapter_block = m.group(1)
        # 章节名
        chapter_name_match = re.match(r'^# (第[一二三四五六七八九十]+章[\s\S]*?)\n', chapter_block)
        chapter_name = chapter_name_match.group(1).strip() if chapter_name_match else ''
        # 图片路径
        images = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', chapter_block)
        # 正文内容（去掉章节名）
        content = chapter_block
        if chapter_name:
            content = content[len('# '+chapter_name):].lstrip('\n')
        chapters.append({
            'chapter_name': chapter_name,
            'images': images,
            'content': content.strip()
        })
    return chapters

def convert_md_to_pkl(md_path, pkl_path):
    """
    将Markdown文件转换为PKL文件的主要函数
    
    Args:
        md_path (str): 输入的Markdown文件路径
        pkl_path (str): 输出的PKL文件路径
        
    Returns:
        bool: 转换是否成功
    """
    try:
        md = read_md(md_path)
        zh_abs, en_abs = extract_abstracts(md)
        ref = extract_reference(md)
        chapters = extract_chapters(md)
        
        data = {
            'zh_abs': zh_abs,
            'en_abs': en_abs,
            'ref': ref,
            'chapters': chapters
        }
        
        # 确保输出目录存在
        os.makedirs(os.path.dirname(pkl_path), exist_ok=True)
        
        with open(pkl_path, 'wb') as f:
            pickle.dump(data, f)
            
        print(f'✓ 转换成功！已保存到: {pkl_path}')
        print(f'  - 中文摘要: {"已提取" if zh_abs else "未找到"}')
        print(f'  - 英文摘要: {"已提取" if en_abs else "未找到"}')
        print(f'  - 参考文献: {"已提取" if ref else "未找到"}')
        print(f'  - 章节数量: {len(chapters)}')
        
        return True
    except Exception as e:
        print(f'✗ 转换失败: {str(e)}')
        return False

def main():
    """
    命令行入口函数
    处理命令行参数并调用转换函数
    """
    parser = argparse.ArgumentParser(
        description='将Markdown文件转换为结构化的PKL格式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            使用示例：
            python md2pkl.py document.md
            python md2pkl.py document.md -o output.pkl
            python md2pkl.py thesis.md --output thesis.pkl
        """
    )
    
    parser.add_argument('md_file', help='输入的Markdown文件路径')
    parser.add_argument('-o', '--output', help='输出的PKL文件路径（默认为输入文件名.pkl）')
    
    args = parser.parse_args()
    
    # 检查输入文件是否存在
    if not os.path.exists(args.md_file):
        print(f'✗ 错误: 输入文件 {args.md_file} 不存在')
        return
    
    # 确定输出路径
    if args.output:
        pkl_path = args.output
    else:
        # 默认输出路径：与输入文件同名但扩展名为.pkl
        pkl_path = os.path.splitext(args.md_file)[0] + '.pkl'
    
    # 执行转换
    print(f'开始转换: {args.md_file} -> {pkl_path}')
    success = convert_md_to_pkl(args.md_file, pkl_path)
    
    if not success:
        exit(1)

if __name__ == '__main__':
    main()
