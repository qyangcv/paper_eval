import re

from utils.helper_utils import get_chapter_idx

def fix_abs_toc(pattern_type: str, text: str):
    """修复摘要和目录部分的匹配问题"""
    abs_cn_re_patterns = [r'#\s*摘\s*要',
               r'摘\s*要']

    abs_eng_re_patterns = [r'#\s*ABSTRACT',
                    r'#\s*BSTRACT',
                    r'#\s*ASTRACT',
                    r'#\s*ABTRACT',
                    r'#\s*ABSRACT',
                    r'#\s*ABSTACT',
                    r'#\s*ABSTRCT',
                    r'#\s*ABSTRAT',
                    r'#\s*ABSTRAC',
                    r'ABSTRACT',
                    r'BSTRACT',
                    r'ASTRACT',
                    r'ABTRACT',
                    r'ABSRACT',
                    r'ABSTACT',
                    r'ABSTRCT',
                    r'ABSTRAT',
                    r'ABSTRAC']

    toc_re_patterns = [r'#\s*目\s*录',
                r'目\s*录']
    
    assert pattern_type in {'abs_cn', 'abs_eng', 'toc'}
    map_dict = {
        'abs_cn': abs_cn_re_patterns,
        'abs_eng': abs_eng_re_patterns,
        'toc': toc_re_patterns
    }
    re_patterns = map_dict[pattern_type] 
     
    for i, pattern in enumerate(re_patterns):
        re_res = re.finditer(pattern, text, re.IGNORECASE)
        all_matches = []
        for m in re_res:
            start_idx = m.start()
            end_idx = m.end()
            match_str = text[start_idx:end_idx]
            all_matches.append([start_idx, match_str])
        if len(all_matches) > 0:
            final_match = all_matches[-1]
            return final_match[0]
    return -1
   
def fix_ref_part(md_text: str, start_idx: int = 0) -> tuple[bool, int]:
    """使用正则找到 参考文献 到 致谢 的内容"""
    print('fixing ref start_idx: ', start_idx)
    md_text = md_text[start_idx:]
    # print('md_text:', md_text[:5000])
    # cn and eng []
    re_patterns = [r'参考文献\s*[\[［]1[\]］](.{0,500}?)\s*[\[［]2[\]］]',
                   r'[\[［]1[\]］](.{0,500}?)\s*[\[［]2[\]］]']
    for i, pattern in enumerate(re_patterns):
        ref_re_res = re.search(pattern, md_text, re.DOTALL)
        if bool(ref_re_res) == False:
            if i == len(re_patterns) - 1:
                return False, None
            else:
                continue
        ref_start_idx = ref_re_res.span()[0]
        # print('fixing...')
        # print('>>>ref_start_idx', ref_start_idx)
        # print(md_text[ref_start_idx: ref_start_idx + 5000])
        ack_re_res = re.search(r'#\s*致\s*谢', md_text[ref_start_idx:])
        if bool(ack_re_res) == False:
            if i == len(re_patterns) - 1:
                return False, None
            else:
                continue
        return True, ref_start_idx + start_idx

def fix_chapter(extract_info, error_idx: int, md_text: str):
    map_dict = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
    start_idx = extract_info['chapters'][error_idx][1]
    end_idx = extract_info['chapters'][error_idx + 1][1]
    
    text = md_text[start_idx:end_idx]
    chapter_idx = get_chapter_idx(text[:100])
    target_idx = chapter_idx + 1

    search_patterns = [f'#\s*第\s*{map_dict[target_idx - 1]}\s*章']
    fix_success = False
    for pattern in search_patterns:
        re_res = re.search(pattern, text)
        if bool(re_res):
            ch_str_idx = re_res.start()
            fix_success = True
            break
    if fix_success == True:
        return f'第{map_dict[target_idx - 1]}章', ch_str_idx + start_idx
    else:
        return '', None
        

def fix_last_chapter(md_text: str, extract_info):
    map_dict = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
    start_idx = extract_info['chapters'][-1][1]
    end_idx = extract_info['ref'][1]
    
    text = md_text[start_idx:end_idx]
    chapter_idx = get_chapter_idx(text[:100])
    target_idx = chapter_idx + 1

    search_patterns = [f'#\s*第\s*{map_dict[target_idx - 1]}\s*章']
    fix_success = False
    for pattern in search_patterns:
        re_res = re.search(pattern, text)
        if bool(re_res):
            ch_str_idx = re_res.start()
            fix_success = True
            break
    if fix_success == True:
        return f'第{map_dict[target_idx - 1]}章', ch_str_idx + start_idx
    else:
        return '', None
        
def check_chapters(chapters: list[dict]):
    """检查章节信息是否完整"""
    chapters = [ch[0] for ch in chapters]
    if get_chapter_idx(chapters[0]) != 1:
        return -1

    for ch, next_ch in zip(chapters, chapters[1:]):
        ch_idx = get_chapter_idx(ch)
        next_ch_idx = get_chapter_idx(next_ch)
        if ch_idx + 1 != next_ch_idx:
            return ch_idx
    return -100
     