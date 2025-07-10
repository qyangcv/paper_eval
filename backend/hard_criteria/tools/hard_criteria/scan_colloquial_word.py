import re
from typing import List

def scan_colloquial_words(text: str) -> List[str]:
    """
    检测输入字符串中是否包含"我"和"我们"，并返回自然语言描述的检测结果
    
    Args:
        text (str): 输入的文本字符串
        
    Returns:
        List[str]: 返回自然语言描述的检测结果列表
    """
    # 定义目标词汇
    target_words = ["我们", "我"]
    
    # 定义句子分隔符的正则表达式
    # 包括中文句号、问号、感叹号、分号、换行符等
    sentence_pattern = r'[。！？；\n]+'
    
    # 分割文本为句子，同时保留分隔符位置信息
    sentences = re.split(sentence_pattern, text)
    
    # 存储结果
    results = []
    
    # 当前位置索引，用于定位句子在原文中的位置
    current_pos = 0
    
    for sentence in sentences:
        # 去除首尾空白字符
        sentence_clean = sentence.strip()
        
        # 跳过空句子
        if not sentence_clean:
            # 更新位置（包括原句子长度和分隔符）
            current_pos += len(sentence)
            # 寻找下一个分隔符的长度
            remaining_text = text[current_pos:]
            delimiter_match = re.match(sentence_pattern, remaining_text)
            if delimiter_match:
                current_pos += len(delimiter_match.group())
            continue
        
        # 找到句子在原文中的位置
        sentence_start = text.find(sentence, current_pos)
        if sentence_start == -1:
            sentence_start = current_pos
        
        # 查找该句子之前最近的章节标题
        text_before_sentence = text[:sentence_start]
        chapter_title, sub_chapter_title = find_nearest_chapter(text_before_sentence)
        
        # 替换标题中的空格为下划线
        chapter_title = chapter_title.replace(" ", "_")
        
        # 如果没有找到小节，则使用章节名代替
        if sub_chapter_title == "未知小节":
            display_sub_title = chapter_title
        else:
            display_sub_title = sub_chapter_title.replace(" ", "_")
        
        # 检查句子中是否包含目标词汇
        # 优先检测"我们"，如果检测到"我们"就不再检测"我"
        description = ""
        if "我们" in sentence_clean:
            # 构造自然语言描述
            description = f"在 {chapter_title} 的 {display_sub_title} 小节的原文 “{sentence_clean}” 中检测到主观用词“我们”"
        elif "我" in sentence_clean:
            # 构造自然语言描述
            description = f"在 {chapter_title} 的 {display_sub_title} 小节的原文 “{sentence_clean}” 中检测到主观用词“我”"
        
        if description:
            results.append(description)
        
        # 更新位置
        current_pos = sentence_start + len(sentence)
        # 寻找下一个分隔符的长度
        remaining_text = text[current_pos:]
        delimiter_match = re.match(sentence_pattern, remaining_text)
        if delimiter_match:
            current_pos += len(delimiter_match.group())
    
    return results


def find_nearest_chapter(text: str) -> tuple[str, str]:
    """
    在给定文本中查找最近的章节标题（一级和二级）
    
    Args:
        text (str): 要搜索的文本
        
    Returns:
        tuple[str, str]: 最近的一级和二级章节标题，如果没找到返回"未知章节"
    """
    # 查找所有一级和二级章节标题
    # 使用 re.MULTILINE 标志，使 `^` 匹配每行的开头
    # 一级标题：以'# '开头，后面不能是'#'
    main_chapter_pattern = r'^\s*#\s+([^#\n].*?)\s*$'
    # 二级标题：以'## '开头，后面不能是'#'
    sub_chapter_pattern = r'^\s*##\s+([^#\n].*?)\s*$'
    
    latest_main_chapter = "未知章节"
    latest_main_pos = -1
    
    # 查找最近的一级标题
    for match in re.finditer(main_chapter_pattern, text, re.MULTILINE):
        if match.start() > latest_main_pos:
            latest_main_pos = match.start()
            latest_main_chapter = match.group(1).strip()
            
    latest_sub_chapter = "未知小节"
    latest_sub_pos = -1
    
    # 查找最近的二级标题（且在最近的一级标题之后）
    for match in re.finditer(sub_chapter_pattern, text, re.MULTILINE):
        if match.start() > latest_main_pos and match.start() > latest_sub_pos:
            latest_sub_pos = match.start()
            latest_sub_chapter = match.group(1).strip()

    return latest_main_chapter, latest_sub_chapter


def print_colloquial_word_sentences(text: str) -> None:
    """
    检测并打印包含"我"和"我们"的句子的自然语言描述
    
    Args:
        text (str): 输入的文本字符串
    """
    results = scan_colloquial_words(text)
    
    if not results:
        print("未检测到包含'我'或'我们'的句子。")
        return
    
    print(f"检测到 {len(results)} 个包含主观用词的句子：")
    print("-" * 60)
    
    for i, description in enumerate(results, 1):
        print(f"{i}. {description}")
        print()


def has_colloquial_words(text: str) -> bool:
    """
    检查文本中是否包含"我"或"我们"
    
    Args:
        text (str): 输入的文本字符串
        
    Returns:
        bool: 如果包含目标词汇返回True，否则返回False
    """
    target_words = ["我", "我们"]
    return any(word in text for word in target_words)


# 示例使用
if __name__ == "__main__":
    # 测试文本
    test_text = """
    # 第一章 引言
    
    这是一个测试文本。我喜欢编程。
    
    ## 1.1 研究背景
    
    我们团队正在开发一个新项目。
    今天天气很好。
    
    ### 1.1.1 具体问题
    
    我们需要完成这个任务。
    他们正在讨论问题。
    
    ## 1.2 研究意义
    
    我认为这个方案可行。
    
    # 第二章 方法
    
    我使用了新的算法。
    """
    
    print("原始文本：")
    print(test_text)
    print("\n" + "="*60 + "\n")
    
    # 调用函数检测并打印结果
    print_colloquial_word_sentences(test_text)
    
    # 也可以只获取结果列表
    results = scan_colloquial_words(test_text)
    print(f"检测结果总数：{len(results)}")
    
    # 检查是否包含目标词汇
    has_words = has_colloquial_words(test_text)
    print(f"是否包含'我'或'我们'：{has_words}")
    
    print("\n详细结果：")
    for i, description in enumerate(results, 1):
        print(f"{i}. {description}")