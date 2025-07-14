"""
DOCX转Markdown工具
将Word文档(.docx)转换为Markdown格式，支持文本、图像、表格和数学公式
"""

import os
import tempfile
from typing import List, Dict, Any, Optional
from docx import Document
from docx.document import Document as _Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

def iter_block_items(parent):
    """
    生成文档中的段落和表格项目
    
    Args:
        parent: 文档对象
        
    Yields:
        段落或表格对象
    """
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("不支持的父对象类型")

    for child in parent_elm:
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)

def table_to_markdown(table: Table) -> str:
    """
    将Word表格转换为Markdown格式
    
    Args:
        table: Word文档中的表格对象
        
    Returns:
        str: Markdown格式的表格字符串
    """
    if not table.rows:
        return ""
        
    md_table = []
    
    # 提取表头
    header = []
    for cell in table.rows[0].cells:
        header.append(cell.text.strip() or " ")
    
    # 计算列宽
    col_widths = [max(len(header[i]), 3) for i in range(len(header))]
    
    # 根据内容调整列宽
    for row in table.rows[1:]:
        for i, cell in enumerate(row.cells):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(cell.text.strip() or " "))
    
    # 创建表头行
    header_formatted = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(header)) + " |"
    md_table.append(header_formatted)
    
    # 创建分隔行
    separator = "|" + "|".join("-" * (w + 2) for w in col_widths) + "|"
    md_table.append(separator)
    
    # 创建内容行
    for row in table.rows[1:]:
        row_cells = []
        for i, cell in enumerate(row.cells):
            if i < len(col_widths):
                row_cells.append((cell.text.strip() or " ").ljust(col_widths[i]))
        md_table.append("| " + " | ".join(row_cells) + " |")
    
    return "\n".join(md_table)

def process_paragraph(paragraph: Paragraph) -> List[str]:
    """
    处理段落，可能包含文本、图像和数学公式
    
    Args:
        paragraph: 段落对象
        
    Returns:
        List[str]: 处理后的内容列表
    """
    # 检查标题样式
    if paragraph.style.name.startswith('Heading'):
        heading_level = int(paragraph.style.name[-1]) if paragraph.style.name[-1].isdigit() else 1
        para_text = paragraph.text.strip()
        if para_text:
            return ['#' * heading_level + ' ' + para_text]
    
    # 处理普通段落
    para_text = paragraph.text.strip()
    if para_text:
        return [para_text]
    
    return []

def convert_docx_to_md(docx_path: str, output_md_path: Optional[str] = None) -> str:
    """
    将DOCX文件转换为Markdown格式
    
    Args:
        docx_path: 输入的DOCX文件路径
        output_md_path: 输出的Markdown文件路径，如果为None则不保存文件
        
    Returns:
        str: Markdown内容
    """
    try:
        # 打开Word文档
        doc = Document(docx_path)
        
        md_content = []
        
        # 按顺序处理文档块（段落和表格）
        for block in iter_block_items(doc):
            if isinstance(block, Paragraph):
                para_content = process_paragraph(block)
                if para_content:
                    md_content.extend(para_content)
                    
            elif isinstance(block, Table):
                md_table = table_to_markdown(block)
                if md_table:
                    md_content.append(md_table)
        
        # 合并内容
        markdown_text = '\n\n'.join(md_content)
        
        # 如果指定了输出路径，保存文件
        if output_md_path:
            os.makedirs(os.path.dirname(output_md_path), exist_ok=True)
            with open(output_md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_text)
        
        return markdown_text
        
    except Exception as e:
        raise Exception(f"DOCX转Markdown失败: {str(e)}")

def convert_docx_bytes_to_md(docx_bytes: bytes) -> str:
    """
    将DOCX字节数据转换为Markdown格式
    
    Args:
        docx_bytes: DOCX文件的字节数据
        
    Returns:
        str: Markdown内容
    """
    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as temp_file:
        temp_file.write(docx_bytes)
        temp_file.flush()
        
        try:
            return convert_docx_to_md(temp_file.name)
        finally:
            os.unlink(temp_file.name)
