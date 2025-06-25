"""
辅助工具模块
提供各种辅助函数
"""

from typing import List, Tuple, Optional
import re

from utils.eval.tools.logger import get_logger

logger = get_logger(__name__)

class StructureError(Exception):
    """结构错误"""
    pass

def text_similarity(a: str, b: str) -> float:
    """计算两个字符串的相似度"""
    return SequenceMatcher(None, a, b).ratio()


def keep_only_chinese_characters(input_string: str) -> str:
    """
    只保留中文字符
    
    Args:
        input_string: 输入字符串
        
    Returns:
        str: 只包含中文字符的字符串
    """
    return "".join(char for char in input_string if '\u4e00' <= char <= '\u9fff')


def check_struct(extract_info: dict) -> Tuple[int, List[str]]:
    """
    检查论文结构是否完整
    
    结构必须包含：
    1. 中文摘要
    2. 英文摘要
    3. 目录
    4. 第一章
    5. 第k章
    6. 参考文献
    7. 致谢
    
    Args:
        extract_info: 提取的信息字典
        
    Returns:
        Tuple[int, List[str]]: (错误代码, 错误信息列表)
            - 错误代码: 0表示无错误，1表示有错误
            - 错误信息列表: 包含缺失的结构项
    """
    error_code = []
    
    # 检查章节数量
    if len(extract_info['chapters']) <= 1:
        logger.warning("章节数量太少")
        return 1, ['章节数量不足']
        
    # 检查第一章
    if '第一章' not in extract_info['chapters'][0][0].replace(' ', ''):
        logger.warning("第一章未匹配")
        error_code.append('第一章')
    
    # 检查其他必要结构
    required_sections = {
        'cn_abs': '中文摘要',
        'eng_abs': '英文摘要',
        'toc': '目录',
        'ack': '致谢',
        'ref': '参考文献'
    }
    
    for key, name in required_sections.items():
        if extract_info.get(key) is None:
            logger.warning(f"{name}未匹配")
            error_code.append(name)
    
    if error_code:
        return 1, error_code
    return 0, []

def validate_chapter_title(title: str) -> bool:
    """
    验证章节标题格式
    
    Args:
        title: 章节标题
        
    Returns:
        bool: 是否为有效的章节标题
    """
    pattern = r'^第[一二三四五六七八九十百千万]+章\s*.*$'
    return bool(re.match(pattern, title))

def extract_chapter_number(title: str) -> Optional[int]:
    """
    从章节标题中提取章节编号
    
    Args:
        title: 章节标题
        
    Returns:
        Optional[int]: 章节编号，如果无法提取则返回None
    """
    chinese_numbers = {
        '一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
        '六': 6, '七': 7, '八': 8, '九': 9, '十': 10
    }
    
    match = re.search(r'第([一二三四五六七八九十]+)章', title)
    if match:
        number = match.group(1)
        return chinese_numbers.get(number)
    return None

def format_chapter_title(title: str) -> str:
    """
    格式化章节标题
    
    Args:
        title: 原始章节标题
        
    Returns:
        str: 格式化后的章节标题
    """
    # 移除多余的空格
    title = re.sub(r'\s+', ' ', title.strip())
    
    # 确保"章"字前没有空格
    title = re.sub(r'第\s+([一二三四五六七八九十]+)\s*章', r'第\1章', title)
    
    return title

def get_chapter_idx(ch):
    map_dict = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
    re_res = re.search('第\s*[一二三四五六七八九十]\s*章', ch[:100])
    match_str = re_res.group(0)
    match_idx = match_str.replace('第', '').replace('章', '').replace(' ', '')
    text_next_num = map_dict.index(match_idx) + 1
    return text_next_num