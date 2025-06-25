import re
import os
from io import StringIO
import pandas as pd

from utils.eval.tools.helper_utils import text_similarity, keep_only_chinese_characters



def clean_cn_abs(txt):
    text_lst = txt.split('\n')
    text_lst = [line.strip() for line in text_lst if line.strip()]
    out = []
    for line in text_lst:
        if (line.startswith('关键词') or line.startswith('关键')) and len(keep_only_chinese_characters(line)) < 25:
            out.append(line)
            break
        out.append(line)
    return "\n".join(out)


def clean_page(text):
    text_lst = text.split('\n')
    text_lst = [line.strip() for line in text_lst if len(line.strip()) > 0]
    out = []
    for text in text_lst:
        if len(text) < 25 and \
            (text_similarity('# 北京邮电大学本科毕业设计(论文)', text) > 0.8 \
            or text_similarity('北京邮电大学本科毕业设计(论文)', text) > 0.8 \
            or text_similarity('# 北京邮电大学本科毕业论文', text) > 0.8 \
            or text_similarity('北京邮电大学本科毕业论文', text) > 0.8):
            continue
        out.append(text)
    return "\n".join(out)

def html_table_to_markdown(html_string):
    def replace_multiple_dashes(text):
        cleaned_text = re.sub(r'-+', '--', text)
        return cleaned_text

    tabels = pd.read_html(StringIO(html_string), header=None)
    df = tabels[0]
    df.columns = df.iloc[0]
    df = df[1:]
    markdown_table_str = df.to_markdown(index=False).replace(' ', '')
    return replace_multiple_dashes(markdown_table_str)

def sub_table(text: str):
    pattern = r"<html>(.*?)</html>"
    all_tables = re.findall(pattern, text)
    
    if len(all_tables) == 0:
        return text, []
    all_tables = [html_table_to_markdown(table) for table in all_tables]
    replaced_text = re.sub(pattern, "<|table_here|>", text)
    return replaced_text, all_tables

# def clean_latex(text: str):
#     pattern = r"\$(.*?)\$"
#     all_inline_latex = re.findall(pattern, text)
    
#     if len(all_inline_latex) == 0:
#         return text, []
#     all_inline_latex = [f"${latex}$" for latex in all_inline_latex]
#     replaced_text = re.sub(pattern, "<|latex_here|>", text)
#     return replaced_text, all_inline_latex

def sub_img(text: str):
    pattern = r"!\[.*?\]\((.*?)\)"
    all_image_paths = re.findall(pattern, text)
    if len(all_image_paths) == 0:
        return text, []
    all_image_paths = [os.path.basename(img_p) for img_p in all_image_paths]
    replaced_text = re.sub(pattern, "<|image_here|>", text)
    return replaced_text, all_image_paths


def get_texts_from_ext_info(extract_info: dict, md_text: str, clean_table: bool) -> dict:
    """使用extract_info 提取文本"""
    cn_abs = md_text[extract_info['cn_abs'][1]: extract_info['eng_abs'][1]]
    eng_abs = md_text[extract_info['eng_abs'][1]: extract_info['toc'][1]]
    ref = md_text[extract_info['ref'][1]: extract_info['ack'][1]]
    chapter_content = []
    for chapter, next_chapter in zip(extract_info['chapters'], extract_info['chapters'][1:]):
        text_content = md_text[chapter[1]: next_chapter[1]]
        text_content, img_paths = sub_img(text_content)
        if clean_table:
            text_content, table_lst = sub_table(text_content)
        else:
            table_lst = []
        chapter_content.append(dict(text_content=clean_page(text_content), img_paths=img_paths, tables=table_lst))
    # 最后一章
    text_content = md_text[extract_info['chapters'][-1][1]: extract_info['ref'][1]]
    text_content, img_paths = sub_img(text_content)
    if clean_table:
        text_content, table_lst = sub_table(text_content)
    else:
        table_lst = []
    chapter_content.append(dict(text_content=clean_page(text_content), img_paths=img_paths, tables=table_lst))
    return {
        'cn_abs': clean_cn_abs(cn_abs),
        'eng_abs': clean_page(eng_abs),
        'ref': clean_page(ref),
        'chapters': chapter_content
    }

def clean_chapter_in_toc(extract_info: dict) -> tuple[dict, list[int]]:
    """将目录 错误解析出来的章节 删去"""
    if extract_info['toc'] is None:
        return extract_info
    toc_start_idx = extract_info['toc'][1]
    start_idx_to_remove = []
    for idx in range(len(extract_info['chapters'])):
        text, start_idx, end_idx = extract_info['chapters'][idx]
        map_dict = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
        re_res = re.match('第\s*[一二三四五六七八九十]\s*章', text)
        match_str = re_res.group(0)
        match_idx = match_str.replace('第', '').replace('章', '').replace(' ', '')
        text_next_num = map_dict.index(match_idx) + 1
        # print(f'inp: {text}, {start_idx}, {end_idx}')
        # print('toc_start_idx:', toc_start_idx)
        # print('text_next_num:', text_next_num)
        # print(f'diff: {start_idx - toc_start_idx}')
        if text_next_num == 1:
            if start_idx - toc_start_idx < 20:
                start_idx_to_remove.append(start_idx)
                # print('should remove:', text)
        else:
            if start_idx - toc_start_idx < 1000 * (text_next_num - 1):
                start_idx_to_remove.append(start_idx)
                # print('should remove:', text)
    lst = [ch for ch in extract_info['chapters'] if ch[1] not in start_idx_to_remove]
    extract_info['chapters'] = lst
    return extract_info
