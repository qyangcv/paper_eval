"""
DOCX转Markdown工具
将Word文档(.docx)转换为Markdown格式，支持文本、图像、表格和数学公式

功能特性：
- 保持文档结构完整性（标题、段落、表格等）
- 自动提取并保存嵌入图像
- 支持数学公式转换（OMML -> LaTeX）
- 表格格式化为Markdown表格
- 按文档顺序处理所有元素
- 支持UTF-8编码输出

依赖要求：
    pip install python-docx

使用方法：
    python docx2md.py <docx文件路径> [选项]
    
命令行参数：
    docx_file           输入的DOCX文件路径（必需）
    -o, --output        输出的Markdown文件路径（可选，默认为输入文件名.md）
    -i, --image_dir     图像保存目录（可选，默认为'images'）

使用示例：
    # 基本用法
    python docx2md.py document.docx
    
    # 指定输出文件和图像目录
    python docx2md.py document.docx -o output.md -i my_images
    
    # 作为模块导入使用
    from docx2md import docx_to_markdown_with_formulas
    docx_to_markdown_with_formulas("input.docx", "output.md", "images")

输出结果：
- 生成的Markdown文件包含完整的文档内容
- 图像文件保存在指定目录中
- 数学公式转换为LaTeX格式
- 表格转换为标准Markdown表格格式

注意事项：
- 确保输入文件为有效的DOCX格式
- 图像目录将自动创建（如果不存在）
- 复杂的数学公式可能需要手动调整
- 某些Word特有的格式可能无法完美转换

作者: PaperEval Team
版本: 1.0.0
"""

import os
from docx import Document
from docx.document import Document as _Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
import argparse
from omml_to_latex import convert_omml_to_latex


def save_image(rel, image_dir, image_id):
    """
    从Word文档关系中保存图像到指定目录
    
    Args:
        rel: Word文档中的图像关系对象
        image_dir (str): 图像保存目录路径
        image_id (int): 图像ID，用于生成文件名
        
    Returns:
        str: 保存的图像文件名，失败时返回None
    """
    try:
        image_bytes = rel.target_part.blob
        image_ext = os.path.splitext(rel.target_ref)[-1]
        if not image_ext:
            image_ext = '.png'  # Default extension if none found
            
        image_filename = f"image_{image_id}{image_ext}"
        image_path = os.path.join(image_dir, image_filename)
        
        with open(image_path, 'wb') as f:
            f.write(image_bytes)
            
        return image_filename
    except Exception as e:
        print(f"Error extracting image: {e}")
        return None


def iter_block_items(parent):
    """
    生成器：按顺序遍历文档中的所有块级元素（段落和表格）
    
    Args:
        parent: Word文档对象或单元格对象
        
    Yields:
        Paragraph or Table: 文档中的段落或表格对象
    """
    if isinstance(parent, _Document):
        parent_elm = parent.element.body
    elif isinstance(parent, _Cell):
        parent_elm = parent._tc
    else:
        raise ValueError("Expected a Document or a Cell")
        
    for child in parent_elm.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, parent)
        elif isinstance(child, CT_Tbl):
            yield Table(child, parent)


def get_element_text(element):
    """Extract text from an XML element."""
    text = ""
    for child in element.iter():
        if child.tag.endswith('}t'):  # Text element in Word XML
            if child.text:
                text += child.text
    return text


def table_to_markdown(table):
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
    
    # Extract header row
    header = []
    for cell in table.rows[0].cells:
        header.append(cell.text.strip() or " ")
    
    # Calculate column widths
    col_widths = [max(len(header[i]), 3) for i in range(len(header))]
    
    # Adjust column widths based on content
    for row in table.rows[1:]:
        for i, cell in enumerate(row.cells):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(cell.text.strip() or " "))
    
    # Create header row
    header_formatted = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(header)) + " |"
    md_table.append(header_formatted)
    
    # Create separator row
    separator = "|" + "|".join("-" * (w + 2) for w in col_widths) + "|"
    md_table.append(separator)
    
    # Create content rows
    for row in table.rows[1:]:
        row_cells = []
        for i, cell in enumerate(row.cells):
            if i < len(col_widths):
                row_cells.append((cell.text.strip() or " ").ljust(col_widths[i]))
        md_table.append("| " + " | ".join(row_cells) + " |")
    
    return "\n".join(md_table)


def find_embedded_image_ids(element):
    """Find embedded image IDs in an element."""
    image_ids = []
    
    # We need to look for drawing elements in the XML
    for child in element.iter():
        if child.tag.endswith('}drawing'):
            # Look for blip elements that contain image references
            for subchild in child.iter():
                if subchild.tag.endswith('}blip'):
                    # Get the embed attribute which is the relationship ID
                    for key, value in subchild.attrib.items():
                        if key.endswith('}embed'):
                            image_ids.append(value)
    
    return image_ids


def extract_math_from_element(element):
    """Extract math elements (OMML) from a paragraph element."""
    math_elements = []
    
    # Look for math elements in the XML
    for child in element.iter():
        if child.tag.endswith('}oMath'):
            math_elements.append(child)
    
    return math_elements


def omml_to_latex_basic(omml_element):
    """Convert OMML (Office Math Markup Language) to LaTeX format using the advanced converter."""
    return convert_omml_to_latex(omml_element)


def process_paragraph_with_math(paragraph, image_dir, image_id_counter, relationship_map):
    """Process a paragraph that may contain text, images, and math formulas."""
    # Check for heading style first
    if paragraph.style.name.startswith('Heading'):
        heading_level = int(paragraph.style.name[-1]) if paragraph.style.name[-1].isdigit() else 1
        para_text = paragraph.text.strip()
        if para_text:
            return ['#' * heading_level + ' ' + para_text]

    # Process the paragraph element directly to maintain order
    result_text = process_paragraph_element_recursively(paragraph._element)

    # Handle images in the paragraph
    image_content = []
    for image_id in find_embedded_image_ids(paragraph._element):
        if image_id in relationship_map:
            rel = relationship_map[image_id]
            image_filename = save_image(rel, image_dir, image_id_counter[0])
            if image_filename:
                # Use absolute path for the image
                image_path = os.path.abspath(os.path.join(image_dir, image_filename))
                # Convert backslashes to forward slashes for markdown compatibility
                image_path = image_path.replace('\\', '/')
                image_content.append(f"![image_{image_id_counter[0]}]({image_path})")
                image_id_counter[0] += 1

    result = []
    if result_text and result_text.strip():
        # Clean up extra spaces
        result_text = ' '.join(result_text.split())
        result.append(result_text)
    result.extend(image_content)

    return result


def print_xml_structure(element, level=0):
    """Print the XML structure of an element for debugging."""
    indent = "  " * level
    tag = element.tag.split('}')[-1] if '}' in element.tag else element.tag
    attrs = []
    for key, value in element.attrib.items():
        key = key.split('}')[-1] if '}' in key else key
        attrs.append(f"{key}='{value}'")
    attrs_str = " ".join(attrs)
    
    if element.text and element.text.strip():
        print(f"{indent}<{tag} {attrs_str}>{element.text.strip()}")
    else:
        print(f"{indent}<{tag} {attrs_str}>")
    
    for child in element:
        print_xml_structure(child, level + 1)
    
    if element.tail and element.tail.strip():
        print(f"{indent}{element.tail.strip()}")


def process_paragraph_element_recursively(element):
    """Recursively process paragraph element to extract text and math in correct order."""
    result_parts = []

    # Process all child elements in order
    for child in element:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

        if tag == 'r':  # Run element
            # Process run content
            run_text = process_run_element(child)
            if run_text:
                result_parts.append(run_text)

        elif tag == 'oMath':  # Math element
            # (debug prints removed)
            
            latex_formula = omml_to_latex_basic(child)
            if latex_formula and latex_formula != "[Math Formula]":
                # Determine if it's inline or display math
                if len(latex_formula) > 50 or any(cmd in latex_formula for cmd in ['\\frac', '\\sum', '\\int', '\\prod']):
                    result_parts.append(f" $$\n{latex_formula}\n$$ ")
                else:
                    result_parts.append(f" ${latex_formula}$ ")

        else:
            # Recursively process other elements
            child_text = process_paragraph_element_recursively(child)
            if child_text:
                result_parts.append(child_text)

    return ''.join(result_parts)


def process_run_element(run_element):
    """Process a run element to extract text and inline math."""
    result_parts = []

    for child in run_element:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

        if tag == 't':  # Text element
            if child.text:
                result_parts.append(child.text)

        elif tag == 'oMath':  # Inline math in run
            latex_formula = omml_to_latex_basic(child)
            if latex_formula and latex_formula != "[Math Formula]":
                # For math in runs, prefer inline format
                result_parts.append(f" ${latex_formula}$ ")

        else:
            # Recursively process other elements
            child_text = process_run_element(child)
            if child_text:
                result_parts.append(child_text)

    return ''.join(result_parts)


def docx_to_markdown_with_formulas(docx_path, output_md_path, image_dir="images"):
    """
    将DOCX文件转换为Markdown格式，保持文本、图像、表格和数学公式的顺序
    
    这是主要的转换函数，处理完整的Word文档转换流程：
    1. 创建图像目录
    2. 解析Word文档结构
    3. 按顺序处理段落和表格
    4. 提取并保存图像
    5. 转换数学公式为LaTeX格式
    6. 生成Markdown文件
    
    Args:
        docx_path (str): 输入的DOCX文件路径
        output_md_path (str): 输出的Markdown文件路径
        image_dir (str): 图像保存目录，默认为"images"
        
    注意：
        - 函数会自动创建图像目录（如果不存在）
        - 支持UTF-8编码，处理中文内容
        - 数学公式会转换为LaTeX格式
    """
    # Create image directory if it doesn't exist
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)
    
    doc = Document(docx_path)
    md_content = []
    
    # Use a counter wrapped in a list to track the image_id through function calls
    image_id_counter = [1]
    formula_count = {'inline': 0, 'display': 0}
    
    # Build a map of relationship IDs to relationships
    relationship_map = {}
    for rel_id, rel in doc.part.rels.items():
        relationship_map[rel_id] = rel
    
    # Process document blocks (paragraphs and tables) in order
    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            para_content = process_paragraph_with_math(block, image_dir, image_id_counter, relationship_map)
            
            # Count formulas for statistics
            for content in para_content:
                if content.startswith('$$') and content.endswith('$$'):
                    formula_count['display'] += 1
                elif '$' in content and not content.startswith('$$'):
                    formula_count['inline'] += content.count('$') // 2
            
            if para_content:
                md_content.extend(para_content)
                
        elif isinstance(block, Table):
            md_table = table_to_markdown(block)
            if md_table:
                md_content.append(md_table)
    
    # Note: All images should be processed within paragraphs above
    # No need to check for remaining images as they are handled in paragraph processing
    
    # Write to markdown file - ensure UTF-8 encoding
    try:
        with open(output_md_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(md_content))
    except UnicodeEncodeError:
        # Fallback to write with explicit error handling
        with open(output_md_path, 'w', encoding='utf-8', errors='xmlcharrefreplace') as f:
            f.write('\n\n'.join(md_content))

def main():
    """
    命令行入口函数
    处理命令行参数并调用转换函数
    """
    parser = argparse.ArgumentParser(
        description='将DOCX文件转换为Markdown格式，支持数学公式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            使用示例：
            python docx2md.py document.docx
            python docx2md.py document.docx -o output.md -i my_images
            python docx2md.py thesis.docx --output thesis.md --image_dir figures
        """
    )
    parser.add_argument('docx_file', help='输入的DOCX文件路径')
    parser.add_argument('-o', '--output', help='输出的Markdown文件路径（可选）')
    parser.add_argument('-i', '--image_dir', default='images', help='图像保存目录（默认：images）')
    
    args = parser.parse_args()
    
    docx_path = args.docx_file
    output_path = args.output if args.output else os.path.splitext(docx_path)[0] + '_with_formulas.md'
    
    docx_to_markdown_with_formulas(docx_path, output_path, args.image_dir)


if __name__ == "__main__":
    main() 