import re

def load_md(md_file: str) -> str:
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def extract_toc(content) -> str:
    # 提取目录部分
    toc_start = content.find('目录')
    toc_end = content.find('# 第一章', toc_start)
    toc = content[toc_start:toc_end].strip() if toc_start != -1 and toc_end != -1 else ""
    # 清理目录内容：去除换行符，合并多个空格
    if toc:
        toc = re.sub(r'\n+', ' ', toc)  # 将一个或多个换行符替换为一个空格
        toc = re.sub(r'\s+', ' ', toc)  # 将多个连续空格合并为一个空格
        toc = toc.strip()
    return toc

def extract_abstract(content) -> dict:
    """
    提取中英文摘要

    Returns:
        dict: 包含中英文摘要的字典，格式为 {"摘要": "中文摘要内容", "Abstract": "英文摘要内容"}
    """
    abstracts = {}
    
    # 提取中文摘要
    zh_abstract_start = content.find('**摘要**')
    if zh_abstract_start != -1:
        # 查找中文摘要结束位置（关键词开始）
        zh_abstract_end = content.find('**关键词**', zh_abstract_start)
        if zh_abstract_end != -1:
            zh_abstract = content[zh_abstract_start:zh_abstract_end].strip()
            # 移除标题
            zh_abstract = re.sub(r'^\*\*摘要\*\*\s*', '', zh_abstract)
            # 清理格式：去除多余换行符，合并空格
            zh_abstract = re.sub(r'\n+', ' ', zh_abstract)
            zh_abstract = re.sub(r'\s+', ' ', zh_abstract)
            abstracts['摘要'] = zh_abstract.strip()
    
    # 提取英文摘要
    en_abstract_start = content.find('**ABSTRACT**')
    if en_abstract_start != -1:
        # 查找英文摘要结束位置（KEY WORDS开始）
        en_abstract_end = content.find('**KEY WORDS**', en_abstract_start)
        if en_abstract_end != -1:
            en_abstract = content[en_abstract_start:en_abstract_end].strip()
            # 移除标题
            en_abstract = re.sub(r'^\*\*ABSTRACT\*\*\s*', '', en_abstract)
            # 清理格式：去除多余换行符，合并空格
            en_abstract = re.sub(r'\n+', ' ', en_abstract)
            en_abstract = re.sub(r'\s+', ' ', en_abstract)
            abstracts['Abstract'] = en_abstract.strip()
    
    return abstracts

def extract_chapters(content) -> dict:
    """
    从Markdown内容中提取各章节内容
    
    提取规则：
    1. 只提取一级标题（#开头）作为主章节
    2. 二级标题（##开头）作为子章节，三级及以下标题（###开头）作为二级标题的内容部分
    4. 自动跳过目录、参考文献、致谢、附录等部分
    
    Args:
        content (str): Markdown文本内容
        
    Returns:
        dict: 章节字典，格式为 {章节名: {'content': 章节全部内容, 'subchapters': {子章节名: 子章节内容}}}
    """
    # 存储所有章节的字典
    chapters = {}
    
    # 只匹配一级标题（大章节）
    sections = re.findall(r'^# (.+?)$', content, re.MULTILINE)
    
    for section in sections:
        if '目录' in section or '参考文献' in section or '致谢' in section or '附录' in section:
            continue
            
        # 提取章节内容 - 从当前章节到下一个一级章节
        section_start = content.find(f'# {section}')
        if section_start == -1:
            continue
            
        # 查找下一个一级标题的位置
        next_section_pattern = r'\n# [^#]'
        next_section_match = re.search(next_section_pattern, content[section_start + 1:])
        
        if next_section_match:
            next_section = section_start + 1 + next_section_match.start()
            section_content = content[section_start:next_section].strip()
        else:
            section_content = content[section_start:].strip()
        
        # 提取二级子章节（只匹配##开头的）
        subsections = re.findall(r'^## (.+?)$', section_content, re.MULTILINE)
        subchapters = {}
        
        for sub in subsections:
            # 在章节内容中查找当前二级标题
            sub_start_pattern = f'^## {re.escape(sub)}$'
            sub_start_match = re.search(sub_start_pattern, section_content, re.MULTILINE)
            
            if not sub_start_match:
                continue
                
            sub_start = sub_start_match.start()
            
            # 查找下一个二级标题的位置
            next_sub_pattern = r'\n## [^#]'
            next_sub_match = re.search(next_sub_pattern, section_content[sub_start + 1:])
            
            if next_sub_match:
                next_sub = sub_start + 1 + next_sub_match.start()
                sub_content = section_content[sub_start:next_sub].strip()
            else:
                # 如果没有下一个二级标题，取到章节结尾
                sub_content = section_content[sub_start:].strip()
            
            subchapters[sub] = sub_content.strip()
        
        chapters[section] = {
            'content': section_content,
            'subchapters': subchapters
        }
    
    return chapters

def extract_references(content) -> str:
    """
    从Markdown内容中提取参考文献部分
    
    Args:
        content (str): Markdown文本内容
        
    Returns:
        str: 提取的参考文献内容，保持原始格式
    """
    # 查找参考文献开始位置
    ref_start = content.find('# 参考文献')
    if ref_start == -1:
        raise ValueError("未找到参考文献部分，请确保文档中包含 '# 参考文献' 标题")
    
    # 查找参考文献结束位置 - 通常是下一个一级标题（如致谢）
    ref_end = content.find('# 致谢', ref_start)
    if ref_end == -1:
        # 如果没有致谢，查找其他可能的结束标志
        ref_end = content.find('# 附录', ref_start)
    if ref_end == -1:
        raise ValueError("未找到参考文献结束位置，请确保文档中包含下一个一级标题")
    
    # 提取参考文献内容
    ref = content[ref_start:ref_end].strip()
    
    # 清理标题部分，只保留参考文献
    ref = re.sub(r'^# 参考文献\s*\n?', '', ref)
    
    # 去除首尾多余的空白，但保留内部格式
    ref = ref.strip()
    
    return ref


def cal_linefeeds(content):
    """
    计算Markdown内容中的换行符数量
    Args:
        content (str): Markdown文本内容
    Returns:
        int: 换行符的数量
    """
    return content.count('\n')



if __name__ == "__main__":
    # 测试代码
    md_path = '/Users/yang/Documents/bupt/code/github/paper_eval/backend/hard_metrics/data/processed/docx/龚礼盛-本科毕业论文.md'
    
    content = load_md(md_path)
    
    # 测试摘要提取
    abstracts = extract_chapters(content)