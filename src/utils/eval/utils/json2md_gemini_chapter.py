"""json2md_gemini_chapter.py
解析 Gemini 章节推理输出（pipeline.chapter_inference 生成）并转换为 Markdown。

用法：
    python utils/json2md_gemini_chapter.py input.json [output.md]

脚本假设输入 JSON 为列表，每条记录结构：
{
    "input": "原始 prompt",
    "output": "<Gemini/DeepSeek/Qwen 响应字符串>"
}
`output` 字段可能有两种形式：
1. OpenAI/DeepSeek 兼容 ChatCompletion JSON（包含 choices[].message.content）。
2. 本地简化实现，直接返回 {"response": "..."}。

真正的章节评价 JSON 位于 content/code block 中，示例：
```json
{
  "章节类型": "绪论",
  ...
}
```

Markdown 结构：
# 章节类型
## 中文表达 (zh)
**概览：** ...
### 详情
1. 原文片段：...
   - 问题分析...
   - 修改建议...

## 英文表达 (en)
...
"""

import json
import re
import sys
import os
from typing import Dict, Any, List

MD_DIM_NAMES = {
    "zh": "中文表达",
    "en": "英文表达",
    "col": "客观性与专业性",
    "for": "公式与符号规范",
    "ref": "参考文献规范",
}

# 章节类别映射到七大核心
CATEGORY_MAP = {
    "中文摘要": "中文摘要",
    "摘要": "中文摘要",
    "英文摘要": "英文摘要",
    "Abstract": "英文摘要",
    "绪论": "绪论",
    "引言": "绪论",
    "研究背景与意义": "绪论",
    "相关技术": "相关技术",
    "文献综述": "相关技术",
    "国内外研究现状": "相关技术",
    "相关工作": "相关技术",
    "理论基础": "相关技术",
    "方法和实验": "方法和实验",
    "研究方法": "方法和实验",
    "实验方案": "方法和实验",
    "实验结果与分析": "方法和实验",
    "数据分析与讨论": "方法和实验",
    "总结和展望": "总结和展望",
    "结论": "总结和展望",
    "研究总结": "总结和展望",
    "未来工作": "总结和展望",
    "参考文献": "参考文献",
}

DIM_ORDER = ["zh", "en", "col", "for", "ref"]

# 提取 ```json ...``` 块
CODE_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)


def _safe_json_loads(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def _extract_content(output_str: str) -> str | None:
    """从 output 字符串中提取章节评价 JSON 字符串。"""
    outer = _safe_json_loads(output_str)
    if not outer:
        return None

    # 形式 1: ChatCompletion
    if isinstance(outer, dict) and "choices" in outer:
        try:
            content = outer["choices"][0]["message"]["content"]
        except Exception:
            return None
    # 形式 2: {"response": "..."}
    elif isinstance(outer, dict) and "response" in outer:
        content = outer["response"]
    else:
        return None

    # 去掉代码块
    m = CODE_BLOCK_RE.search(content)
    if m:
        content = m.group(1)
    return content


def load_chapter_evals(path: str) -> Dict[str, Dict[str, Dict[str, Any]]]:
    with open(path, "r", encoding="utf-8") as f:
        records: List[Dict[str, Any]] = json.load(f)

    chapters: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for rec in records:
        output_str = rec.get("output")
        if not output_str:
            continue
        content_json_str = _extract_content(output_str)
        if not content_json_str:
            continue
        eval_data = _safe_json_loads(content_json_str)
        if not eval_data:
            continue

        raw_chapter = eval_data.get("章节类型", "未知章节").strip()
        chapter_type = CATEGORY_MAP.get(raw_chapter, raw_chapter)
        eval_dict = eval_data.get("评价", {})
        if not chapters.get(chapter_type):
            chapters[chapter_type] = {}
        for dim, dim_val in eval_dict.items():
            # 若同章节同维度出现多次，合并详情列表
            if dim in chapters[chapter_type]:
                prev = chapters[chapter_type][dim]
                # 合并概览：保留首次概览或更新为更长文本
                if len(dim_val.get("概览", "")) > len(prev.get("概览", "")):
                    prev["概览"] = dim_val.get("概览", "")
                prev_details = prev.get("详情", [])
                new_details = dim_val.get("详情", [])
                prev_details.extend(new_details)
                prev["详情"] = prev_details
            else:
                chapters[chapter_type][dim] = dim_val
    return chapters


def write_md(chapters: Dict[str, Dict[str, Dict[str, Any]]], out_path: str):
    with open(out_path, "w", encoding="utf-8") as f:
        for chapter, dims in chapters.items():
            f.write(f"# {chapter}\n\n")
            for dim in DIM_ORDER:
                dim_name = MD_DIM_NAMES.get(dim, dim)
                f.write(f"## {dim_name} ({dim})\n\n")
                data = dims.get(dim)
                if not data:
                    f.write("*无该维度数据*\n\n")
                    continue
                overview = data.get("概览", "")
                if overview:
                    f.write(f"**概览：**{overview}\n\n")
                details = data.get("详情", [])
                if details:
                    f.write("### 详情\n\n")
                    for item in details:
                        idx = item.get("序号", "-")
                        snippet = item.get("原文片段", "")
                        analysis = item.get("问题分析", "")
                        suggestion = item.get("修改建议", "")
                        f.write(f"{idx}. 原文片段：{snippet}\n\n   - 问题分析：{analysis}\n\n   - 修改建议：{suggestion}\n\n")
                f.write("\n")


def main():
    if len(sys.argv) < 2:
        print("用法: python json2md_gemini_chapter.py input.json [output.md]")
        sys.exit(1)
    in_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(in_path)[0] + ".md"

    chapters = load_chapter_evals(in_path)
    write_md(chapters, out_path)
    print(f"已生成 Markdown 文件: {out_path}")


if __name__ == "__main__":
    main() 