"""json2md_ds_v3_batch.py
解析 DeepSeek v3 批量推理结果，将同章节同维度的 content 合并为 Markdown。

用法：
    python utils/json2md_ds_v3_batch.py input.json [output.md]
"""

import json
import re
import sys
import os
from typing import Dict, Any, List

DIM_ORDER = ["zh", "en", "col", "for", "ref"]
DIM_CN = {
    "zh": "中文表达",
    "en": "英文表达",
    "col": "客观性与专业性",
    "for": "公式与符号规范",
    "ref": "参考文献规范",
}

CODE_BLOCK_RE = re.compile(r"```json\s*(\{.*?\})\s*```", re.S)


def _safe_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def _extract_json_from_output(output: str) -> Dict[str, Any] | None:
    outer = _safe_json(output)
    if not outer or not isinstance(outer, dict):
        return None
    try:
        content = outer["choices"][0]["message"]["content"]
    except Exception:
        return None

    m = CODE_BLOCK_RE.search(content)
    if m:
        content = m.group(1)
    return _safe_json(content)


def load_records(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def aggregate(records: List[Dict[str, Any]]):
    chapters: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    for rec in records:
        output_str = rec.get("output")
        if not output_str:
            continue
        data = _extract_json_from_output(output_str)
        if not data:
            continue
        chapter = data.get("章节类型", "未知章节").strip()
        evals = data.get("评价", {})
        chap_dict = chapters.setdefault(chapter, {d: [] for d in DIM_ORDER})
        for dim in DIM_ORDER:
            if dim in evals:
                chap_dict[dim].append(evals[dim])
    return chapters


def merge_dimension(detail_list: List[Dict[str, Any]]):
    if not detail_list:
        return None
    # 合并概览(取最长)
    overview = max((d.get("概览", "") for d in detail_list), key=len, default="")
    details: List[Any] = []
    for d in detail_list:
        details.extend(d.get("详情", []))
    return {"概览": overview, "详情": details}


def write_markdown(chapters: Dict[str, Dict[str, List[Dict[str, Any]]]], out_path: str):
    with open(out_path, "w", encoding="utf-8") as f:
        for chap, dims in chapters.items():
            f.write(f"# {chap}\n\n")
            for dim in DIM_ORDER:
                merged = merge_dimension(dims.get(dim, []))
                dim_cn = DIM_CN[dim]
                f.write(f"## {dim_cn} ({dim})\n\n")
                if not merged:
                    f.write("*无该维度数据*\n\n")
                    continue
                overview = merged.get("概览", "")
                if overview:
                    f.write(f"**概览：**{overview}\n\n")
                details = merged.get("详情", [])
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
        print("用法: python utils/json2md_ds_v3_batch.py input.json [output.md]")
        sys.exit(1)
    in_path = sys.argv[1]
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(in_path)[0] + ".md"

    records = load_records(in_path)
    chapters = aggregate(records)
    write_markdown(chapters, out_path)
    print(f"已生成 Markdown 文件: {out_path}")


if __name__ == "__main__":
    main() 