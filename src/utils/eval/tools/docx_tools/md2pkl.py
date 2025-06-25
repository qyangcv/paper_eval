import re
import os
import pickle

MD_PATH = 'data/processed/docx/<xxx>.md'
PKL_PATH = 'data/processed/docx/<xxx>.pkl'

# 读取markdown内容
def read_md(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_abstracts(md):
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
    ref = ''
    ref_match = re.search(r'# 参考文献\n([\s\S]*?)(?=\n# |\Z)', md)
    if ref_match:
        ref = ref_match.group(1).strip()
    return ref

def extract_chapters(md):
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

def main():
    md = read_md(MD_PATH)
    zh_abs, en_abs = extract_abstracts(md)
    ref = extract_reference(md)
    chapters = extract_chapters(md)
    data = {
        'zh_abs': zh_abs,
        'en_abs': en_abs,
        'ref': ref,
        'chapters': chapters
    }
    with open(PKL_PATH, 'wb') as f:
        pickle.dump(data, f)
    print(f'已保存到 {PKL_PATH}')

def convert_md_to_pkl(md_path, pkl_path):
    """
    对外的函数接口，将Markdown文件转换为PKL文件
    
    Args:
        md_path: Markdown文件路径
        pkl_path: 输出的PKL文件路径
        
    Returns:
        bool: 是否转换成功
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
            
        print(f'已保存到 {pkl_path}')
        return True
    except Exception as e:
        print(f"转换MD到PKL失败: {str(e)}")
        return False

if __name__ == '__main__':
    main()
