"""
解析工具模块
提供各种文本解析功能
"""

from typing import List, Dict, Optional, Tuple
import re
from difflib import SequenceMatcher

from logger import get_logger

logger = get_logger(__name__)

class ParseError(Exception):
    """解析错误"""
    pass

def text_similarity(a: str, b: str) -> float:
    """
    计算两个字符串的相似度
    
    Args:
        a: 第一个字符串
        b: 第二个字符串
        
    Returns:
        float: 相似度分数，范围[0,1]
    """
    return SequenceMatcher(None, a, b).ratio()

def match_abs_eng(text: str) -> bool:
    """
    检查文本是否匹配英文摘要
    
    Args:
        text: 输入文本
        
    Returns:
        bool: 是否匹配英文摘要
    """
    def text_iou(a: str, b: str) -> float:
        """
        计算两个字符串的IoU（交并比）
        
        Args:
            a: 第一个字符串
            b: 第二个字符串
            
        Returns:
            float: IoU分数，范围[0,1]
        """
        intersection = len(set(a) & set(b))
        union = len(set(a) | set(b))
        return intersection / union if union > 0 else 0.0
        
    return text_iou(text.lower(), 'abstract') > 0.8

def extract_section_title(text: str) -> Optional[str]:
    """
    从文本中提取章节标题
    
    Args:
        text: 输入文本
        
    Returns:
        Optional[str]: 提取的章节标题，如果未找到则返回None
    """
    pattern = r'^第[一二三四五六七八九十百千万]+章\s*.*$'
    match = re.match(pattern, text.strip())
    return match.group(0) if match else None

def parse_reference(text: str) -> List[Dict[str, str]]:
    """
    解析参考文献
    
    Args:
        text: 参考文献文本
        
    Returns:
        List[Dict[str, str]]: 解析后的参考文献列表
    """
    references = []
    current_ref = {}
    
    # 分割参考文献
    ref_blocks = re.split(r'\[\d+\]', text)[1:]  # 跳过第一个空字符串
    
    for block in ref_blocks:
        block = block.strip()
        if not block:
            continue
            
        # 提取作者
        authors_match = re.search(r'^([^,]+),', block)
        if authors_match:
            current_ref['authors'] = authors_match.group(1).strip()
            
        # 提取标题
        title_match = re.search(r'"([^"]+)"', block)
        if title_match:
            current_ref['title'] = title_match.group(1).strip()
            
        # 提取期刊/会议
        venue_match = re.search(r'《([^》]+)》', block)
        if venue_match:
            current_ref['venue'] = venue_match.group(1).strip()
            
        # 提取年份
        year_match = re.search(r'(\d{4})', block)
        if year_match:
            current_ref['year'] = year_match.group(1)
            
        if current_ref:
            references.append(current_ref.copy())
            current_ref.clear()
            
    return references

def extract_keywords(text: str) -> List[str]:
    """
    从文本中提取关键词
    
    Args:
        text: 输入文本
        
    Returns:
        List[str]: 关键词列表
    """
    # 移除标点符号和特殊字符
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # 分割成单词
    words = text.split()
    
    # 过滤掉停用词和短词
    stop_words = {'的', '了', '和', '是', '在', '有', '与', '这', '那', '都', '也', '而', '但', '并'}
    keywords = [word for word in words if len(word) > 1 and word not in stop_words]
    
    return keywords

def validate_text_structure(text: str) -> Tuple[bool, List[str]]:
    """
    验证文本结构
    
    Args:
        text: 输入文本
        
    Returns:
        Tuple[bool, List[str]]: (是否有效, 错误信息列表)
    """
    errors = []
    
    # 检查段落数量
    paragraphs = text.split('\n\n')
    if len(paragraphs) < 3:
        errors.append("段落数量不足")
        
    # 检查句子长度
    sentences = re.split(r'[。！？]', text)
    long_sentences = [s for s in sentences if len(s) > 100]
    if long_sentences:
        errors.append(f"存在{len(long_sentences)}个过长的句子")
        
    # 检查标点符号使用
    if re.search(r'[，。！？]{2,}', text):
        errors.append("存在重复的标点符号")
        
    return len(errors) == 0, errors

def extract_h1_titles(markdown_content: str) -> list:
    md = MarkdownIt()
    h1_titles = []
    tokens = md.parse(markdown_content)

    for i, token in enumerate(tokens):
        # 查找 'heading' 类型的 token
        if token.type == 'heading_open' and token.tag == 'h1':
            # 确保下一个 token 是 'inline' 类型的，它包含标题文本
            if i + 1 < len(tokens) and tokens[i+1].type == 'inline':
                h1_titles.append(tokens[i+1].content)
    return h1_titles

def extract_h1_titles_re(markdown_text: str) -> list:
    """提取所有一级标题"""
    pattern = re.compile(r"^#\s(.*)$", re.MULTILINE)
    re_res = pattern.finditer(markdown_text)
    lst = []
    for res in re_res:
        start_idx = res.start()
        end_idx = res.end()
        title = res.group(1).strip()
        lst.append((title, start_idx, end_idx))
    return lst

def match_abs_cn(text: str) -> bool:
    return text == '摘要'

def match_toc(text: str) -> bool:
    return text == '目录'

def match_ref(text: str) -> bool:
    return text == '参考文献'

def match_ack(text: str) -> bool:
    return text == '致谢'

def match_chapter(text: str, next_text: str) -> bool:
    """章节匹配规则：
    第k章 xxx 下一个必须是 k.1 xxx"""
    map_dict = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
    re_res = re.match(r'第\s*[一二三四五六七八九十]\s*章', text)
    if bool(re_res) == False:
        return False
    match_str = re_res.group(0)
    match_idx = match_str.replace('第', '').replace('章', '').replace(' ', '')
    text_next_num = map_dict.index(match_idx) + 1
    re_res = re.match(fr'^{text_next_num}\s*\.\s*[1,2]', next_text)
    if bool(re_res):
        return True
    return False