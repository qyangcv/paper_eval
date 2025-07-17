"""
DOCX转HTML工具
将Word文档(.docx)转换为HTML格式，支持文本、图像、表格和数学公式

功能特性：
- 保持文档结构完整性（标题、段落、表格等）
- 自动提取并保存嵌入图像
- 支持数学公式转换（OMML -> LaTeX）
- 表格格式化为HTML表格
- 按文档顺序处理所有元素
- 支持UTF-8编码输出
- 生成完整的HTML文档结构
- 后处理1：去除特定条件下段落的段首空格
- 后处理2：去除所有斜体标签

依赖要求：
    pip install python-docx

使用方法：
    python docx2html.py <docx文件路径> [选项]
    
命令行参数：
    docx_file           输入的DOCX文件路径（必需）
    -o, --output        输出的HTML文件路径（可选，默认为输入文件名.html）
    -i, --image_dir     图像保存目录（可选，默认为'images'）
    -c, --css           自定义CSS文件路径（可选）

使用示例：
    # 基本用法
    python docx2html.py document.docx
    
    # 指定输出文件和图像目录
    python docx2html.py document.docx -o output.html -i my_images
    
    # 添加自定义CSS样式
    python docx2html.py document.docx -c styles.css

输出结果：
- 完整的HTML5文档
- 图像文件保存在指定目录中
- 数学公式转换为LaTeX格式
- 表格转换为标准HTML表格格式
- 默认包含基础CSS样式，支持自定义样式
- 满足特定条件下自动去除段首空格
- 所有斜体标签(<em>)被移除

注意事项：
- 确保输入文件为有效的DOCX格式
- 图像目录将自动创建（如果不存在）
- 复杂的数学公式可能需要手动调整
- 某些Word特有的格式可能无法完美转换

作者: PaperEval Team
版本: 1.3.0
新增功能：
    1.2.0: 后处理去除特定条件下段落的段首空格
    1.3.0: 后处理去除所有斜体标签
"""

import os
import argparse
import re
import base64
from docx import Document
from docx.document import Document as _Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from .omml_to_latex import convert_omml_to_latex

# 默认CSS样式 - 增强列表样式
DEFAULT_CSS = """
/* 基础文档样式 */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
}

/* 标题样式 */
h1, h2, h3, h4, h5, h6 {
    color: #2c3e50;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    font-weight: 600;
}

h1 { font-size: 2.2em; }
h2 { font-size: 1.8em; }
h3 { font-size: 1.5em; }
h4 { font-size: 1.3em; }
h5 { font-size: 1.1em; }
h6 { font-size: 1em; }

/* 段落样式 */
p {
    margin: 0 0 1em 0;
    text-align: justify;
}

/* 列表样式 - 增强 */
ul, ol {
    margin: 0 0 1em 1.5em;
    padding: 0;
}

li {
    margin-bottom: 0.8em;
    position: relative;
    list-style: none; /* 移除默认列表标记 */
}

/* 无序列表标记样式 */
ul li::before {
    content: "•";
    color: #3498db;
    position: absolute;
    left: -1.5em;
    font-size: 1.2em;
}

/* 有序列表计数器 */
ol {
    counter-reset: list-counter;
    margin-left: 1.8em;
}

ol li {
    counter-increment: list-counter;
    position: relative;
}

ol li::before {
    content: counter(list-counter) ".";
    position: absolute;
    left: -1.8em;
    width: 1.5em;
    text-align: right;
    font-weight: bold;
    color: #3498db;
}

/* 字母序号列表 */
ol.alpha-lower li::before {
    content: counter(list-counter, lower-alpha) ".";
}

ol.alpha-upper li::before {
    content: counter(list-counter, upper-alpha) ".";
}

/* 罗马数字序号列表 */
ol.roman-lower li::before {
    content: counter(list-counter, lower-roman) ".";
}

ol.roman-upper li::before {
    content: counter(list-counter, upper-roman) ".";
}

/* 表格样式 */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
    box-shadow: 0 0 10px rgba(0,0,0,0.05);
}

th, td {
    padding: 10px 15px;
    text-align: left;
    border: 1px solid #ddd;
}

th {
    background-color: #f8f9fa;
    font-weight: 600;
}

tr:nth-child(even) {
    background-color: #f9f9f9;
}

/* 图片样式 */
img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 1em auto;
    border-radius: 4px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

/* 数学公式样式 */
.math {
    margin: 1em 0;
    text-align: center;
    padding: 10px;
    background-color: #f8f9fa;
    border-radius: 4px;
    overflow-x: auto;
}

.math-inline {
    display: inline;
    padding: 2px 5px;
}

/* 引用块样式 */
blockquote {
    border-left: 4px solid #3498db;
    padding: 10px 20px;
    margin: 1em 0;
    background-color: #f9f9f9;
    color: #555;
    font-style: italic;
}

/* 对齐样式 */
.text-left {
    text-align: left;
}

.text-center {
    text-align: center;
}

.text-right {
    text-align: right;
}

.text-justify {
    text-align: justify;
}
"""


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
        image_ext = os.path.splitext(rel.target_ref)[-1].lower()
        if not image_ext or image_ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            image_ext = '.png'  # 默认使用PNG格式

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
    """从XML元素提取文本"""
    text = ""
    for child in element.iter():
        if child.tag.endswith('}t'):  # Word XML中的文本元素
            if child.text:
                text += child.text
    return text


def table_to_html(table):
    """
    将Word表格转换为HTML格式

    Args:
        table: Word文档中的表格对象

    Returns:
        str: HTML格式的表格字符串
    """
    if not table.rows:
        return ""

    html_table = ['<table>']

    # 处理表头
    if table.rows and any(cell.text.strip() for cell in table.rows[0].cells):
        html_table.append('  <thead>')
        html_table.append('    <tr>')
        for cell in table.rows[0].cells:
            cell_text = cell.text.strip() or "&nbsp;"
            html_table.append(f'      <th>{cell_text}</th>')
        html_table.append('    </tr>')
        html_table.append('  </thead>')

    # 处理表格内容
    html_table.append('  <tbody>')
    for row in table.rows[1:]:
        html_table.append('    <tr>')
        for cell in row.cells:
            cell_text = cell.text.strip() or "&nbsp;"
            html_table.append(f'      <td>{cell_text}</td>')
        html_table.append('    </tr>')
    html_table.append('  </tbody>')

    html_table.append('</table>')
    return '\n'.join(html_table)


def find_embedded_image_ids(element):
    """在元素中查找嵌入图像ID"""
    image_ids = []

    # 在XML中查找绘图元素
    for child in element.iter():
        if child.tag.endswith('}drawing'):
            # 查找包含图像引用的blip元素
            for subchild in child.iter():
                if subchild.tag.endswith('}blip'):
                    # 获取embed属性（关系ID）
                    for key, value in subchild.attrib.items():
                        if key.endswith('}embed'):
                            image_ids.append(value)

    return image_ids


def extract_math_from_element(element):
    """从段落元素提取数学元素(OMML)"""
    math_elements = []

    # 在XML中查找数学元素
    for child in element.iter():
        if child.tag.endswith('}oMath'):
            math_elements.append(child)

    return math_elements


def omml_to_latex_basic(omml_element):
    """使用高级转换器将OMML转换为LaTeX格式"""
    return convert_omml_to_latex(omml_element)


def get_paragraph_alignment(paragraph):
    """获取段落对齐方式"""
    if paragraph.alignment == WD_ALIGN_PARAGRAPH.CENTER:
        return "center"
    elif paragraph.alignment == WD_ALIGN_PARAGRAPH.RIGHT:
        return "right"
    elif paragraph.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY:
        return "justify"
    else:  # 包括LEFT和None
        return "left"


def get_list_numbering_format(paragraph):
    """
    获取有序列表的序号格式

    Args:
        paragraph: Word段落对象

    Returns:
        tuple: (序号格式, 起始序号)
    """
    # 默认值
    num_format = "decimal"
    start = 1

    # 查找numPr元素
    num_pr = paragraph._element.find(qn('w:numPr'))
    if num_pr is not None:
        # 获取编号ID
        num_id = num_pr.find(qn('w:numId'))
        if num_id is not None:
            num_id_val = num_id.get(qn('w:val'))

            # 在文档中查找编号定义
            numbering = paragraph.part.numbering_part.numbering_definitions
            for num in numbering.num_lst:
                if num.numId == int(num_id_val):
                    # 获取抽象编号ID
                    abstract_num_id = num.abstractNumId.val

                    # 查找抽象编号定义
                    for abstract_num in numbering.abstractNum_lst:
                        if abstract_num.abstractNumId == abstract_num_id:
                            # 获取层级
                            lvl = num_pr.find(qn('w:ilvl'))
                            lvl_idx = int(lvl.get(qn('w:val'))
                                          ) if lvl is not None else 0

                            # 获取该层级的格式
                            for lvl_elem in abstract_num.lvl_lst:
                                if lvl_elem.ilvl == lvl_idx:
                                    # 获取编号格式
                                    num_fmt = lvl_elem.find(qn('w:numFmt'))
                                    if num_fmt is not None:
                                        fmt_val = num_fmt.get(qn('w:val'))
                                        if fmt_val == "decimal":
                                            num_format = "decimal"
                                        elif fmt_val == "lowerLetter":
                                            num_format = "alpha-lower"
                                        elif fmt_val == "upperLetter":
                                            num_format = "alpha-upper"
                                        elif fmt_val == "lowerRoman":
                                            num_format = "roman-lower"
                                        elif fmt_val == "upperRoman":
                                            num_format = "roman-upper"
                                        # 其他格式可以继续添加

                                    # 获取起始序号
                                    start_override = num.find(
                                        qn('w:startOverride'))
                                    if start_override is not None:
                                        start_val = start_override.get(
                                            qn('w:val'))
                                        if start_val is not None:
                                            try:
                                                start = int(start_val)
                                            except:
                                                start = 1
                                    break
                            break
                    break

    return num_format, start


def process_paragraph_with_math(paragraph, image_dir, image_id_counter, relationship_map):
    """处理可能包含文本、图像和数学公式的段落"""
    # 首先检查标题样式
    if paragraph.style.name.startswith('Heading'):
        heading_level = int(
            paragraph.style.name[-1]) if paragraph.style.name[-1].isdigit() else 1
        heading_level = min(max(heading_level, 1), 6)  # 确保在1-6范围内
        return [f'<h{heading_level}>{paragraph.text.strip()}</h{heading_level}>']

    # 处理列表 - 增强有序列表处理
    if paragraph.style.name.startswith('List'):
        # 获取列表类型和格式
        if "Number" in paragraph.style.name or "Bullet" not in paragraph.style.name:
            list_type = "ol"
            num_format, start_num = get_list_numbering_format(paragraph)
        else:
            list_type = "ul"
            num_format = None
            start_num = 1

        # 获取列表项内容
        list_content = process_paragraph_element_recursively(
            paragraph._element)

        # 获取对齐方式
        alignment = get_paragraph_alignment(paragraph)
        align_class = f"text-{alignment}"

        # 创建列表项
        list_item = f'<li class="{align_class}">{list_content}</li>'
        return [list_item, list_type, num_format, start_num]

    # 处理引用
    if paragraph.style.name == 'Quote':
        return [f'<blockquote>{process_paragraph_element_recursively(paragraph._element)}</blockquote>']

    # 处理普通段落
    para_content = process_paragraph_element_recursively(paragraph._element)

    # 处理段落中的图像
    image_content = []
    for image_id in find_embedded_image_ids(paragraph._element):
        if image_id in relationship_map:
            rel = relationship_map[image_id]
            image_filename = save_image(rel, image_dir, image_id_counter[0])
            if image_filename:
                # 使用相对路径，只包含images目录和文件名
                image_relative_path = f"images/{image_filename}"
                image_content.append(
                    f'<img src="{image_relative_path}" alt="image_{image_id_counter[0]}">')
                image_id_counter[0] += 1

    # 获取对齐方式
    alignment = get_paragraph_alignment(paragraph)
    align_class = f"text-{alignment}"

    result = []
    if para_content and para_content.strip():
        # 添加段首空两格（两个全角空格）
        indented_content = f'&#12288;&#12288;{para_content}'
        result.append(f'<p class="{align_class}">{indented_content}</p>')
    result.extend(image_content)

    return result


def process_paragraph_element_recursively(element):
    """递归处理段落元素以按正确顺序提取文本和数学公式"""
    result_parts = []

    # 按顺序处理所有子元素
    for child in element:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

        if tag == 'r':  # 文本运行元素
            # 处理运行内容
            run_text = process_run_element(child)
            if run_text:
                result_parts.append(run_text)

        elif tag == 'oMath':  # 数学元素
            latex_formula = omml_to_latex_basic(child)
            if latex_formula and latex_formula != "[Math Formula]":
                # 确定是行内公式还是块级公式
                if len(latex_formula) > 50 or any(cmd in latex_formula for cmd in ['\\frac', '\\sum', '\\int', '\\prod']):
                    result_parts.append(
                        f'<div class="math">\[{latex_formula}\]</div>')
                else:
                    result_parts.append(
                        f'<span class="math-inline">\({latex_formula}\)</span>')

        else:
            # 递归处理其他元素
            child_text = process_paragraph_element_recursively(child)
            if child_text:
                result_parts.append(child_text)

    return ''.join(result_parts)


def process_run_element(run_element):
    """处理运行元素以提取文本和内联数学公式"""
    result_parts = []

    for child in run_element:
        tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag

        if tag == 't':  # 文本元素
            if child.text:
                result_parts.append(child.text)

        elif tag == 'oMath':  # 运行中的内联数学
            latex_formula = omml_to_latex_basic(child)
            if latex_formula and latex_formula != "[Math Formula]":
                result_parts.append(
                    f'<span class="math-inline">\({latex_formula}\)</span>')

        else:
            # 递归处理其他元素
            child_text = process_run_element(child)
            if child_text:
                result_parts.append(child_text)

    # 处理文本格式（粗体、斜体等）
    formatted_text = ''.join(result_parts)

    # 检查运行格式（仅当存在rPr属性时）
    if hasattr(run_element, 'rPr'):
        run_format = run_element.rPr

        # 使用显式检查避免 FutureWarning
        if run_format is not None:
            # 粗体
            if getattr(run_format, 'b', None) is not None or getattr(run_format, 'bCs', None) is not None:
                formatted_text = f'<strong>{formatted_text}</strong>'
            # 斜体
            # 注释掉斜体处理，因为最后会统一移除所有斜体标签
            # if getattr(run_format, 'i', None) is not None or getattr(run_format, 'iCs', None) is not None:
            #     formatted_text = f'<em>{formatted_text}</em>'
            # 下划线
            if getattr(run_format, 'u', None) is not None:
                formatted_text = f'<u>{formatted_text}</u>'
            # 上标
            if (getattr(run_format, 'vertAlign', None) is not None and
                    getattr(run_format.vertAlign, 'val', None) == 'superscript'):
                formatted_text = f'<sup>{formatted_text}</sup>'
            # 下标
            if (getattr(run_format, 'vertAlign', None) is not None and
                    getattr(run_format.vertAlign, 'val', None) == 'subscript'):
                formatted_text = f'<sub>{formatted_text}</sub>'

    return formatted_text


def remove_leading_space_after_math(html_content):
    """
    后处理HTML内容：如果块级公式后的段落以特定字开头，则去除段首空格

    Args:
        html_content (str): HTML内容字符串

    Returns:
        str: 处理后的HTML内容
    """
    # 将HTML内容按行分割
    lines = html_content.split('\n')

    # 初始化变量
    processed_lines = []
    prev_was_math = False

    # 遍历每一行
    for i, line in enumerate(lines):
        # 检查是否为块级数学公式结束标签
        if '</div>' in line and '<div class="math">' in line:
            # 标记前一个区块是数学公式
            prev_was_math = True
            processed_lines.append(line)
            continue

        # 检查当前行是否为段落开始
        if line.strip().startswith('<p'):
            # 检查前一个区块是否为数学公式
            if prev_was_math:
                # 检查段落内容是否以特定字开头
                if re.search(r'<p[^>]*>\s*&#12288;&#12288;([其并或])', line):
                    # 去除段首空格
                    line = re.sub(
                        r'(<p[^>]*>)\s*&#12288;&#12288;', r'\1', line)
                    # 打印调试信息
                    print(f"已去除段首空格: 行 {i+1}")

            # 重置前一个区块状态
            prev_was_math = False
        else:
            # 如果不是段落开始行，重置前一个区块状态
            prev_was_math = False

        processed_lines.append(line)

    return '\n'.join(processed_lines)


def remove_italic_tags(html_content):
    """
    后处理HTML内容：移除所有斜体标签（<em>和</em>）

    Args:
        html_content (str): HTML内容字符串

    Returns:
        str: 处理后的HTML内容（已移除所有斜体标签）
    """
    # 使用正则表达式移除所有斜体标签
    # 注意：我们只移除标签本身，保留标签内的内容
    html_content = re.sub(r'</?em>', '', html_content)

    # 打印处理信息
    print(f"已移除所有斜体标签")

    return html_content


def docx_to_html(docx_path, output_html_path, image_dir="images", css_file=None):
    """
    将DOCX文件转换为HTML格式，保持文本、图像、表格和数学公式的顺序

    主要转换流程：
    1. 创建图像目录
    2. 解析Word文档结构
    3. 按顺序处理段落和表格
    4. 提取并保存图像
    5. 转换数学公式为LaTeX格式
    6. 生成完整的HTML文档
    7. 后处理1：去除特定条件下段落的段首空格
    8. 后处理2：去除所有斜体标签

    Args:
        docx_path (str): 输入的DOCX文件路径
        output_html_path (str): 输出的HTML文件路径
        image_dir (str): 图像保存目录，默认为"images"
        css_file (str): 自定义CSS文件路径，可选

    注意：
        - 自动创建图像目录（如果不存在）
        - 支持UTF-8编码，处理中文内容
        - 数学公式转换为LaTeX格式
        - 生成完整的HTML5文档结构
        - 后处理满足特定条件的段落
        - 后处理移除所有斜体标签
    """
    # 创建图像目录
    if not os.path.exists(image_dir):
        os.makedirs(image_dir)

    doc = Document(docx_path)
    html_content = []

    # 使用列表包装计数器以通过函数调用跟踪image_id
    # 从0开始计数，确保与实际保存的文件名一致
    image_id_counter = [0]

    # 构建关系ID到关系的映射
    relationship_map = {}
    for rel_id, rel in doc.part.rels.items():
        relationship_map[rel_id] = rel

    # 按顺序处理文档块（段落和表格）
    in_list = False
    current_list_type = None  # 当前列表类型（'ul'或'ol'）
    current_list_format = None  # 当前列表格式
    current_list_start = 1  # 当前列表起始序号
    list_start_set = False  # 起始序号是否已设置

    for block in iter_block_items(doc):
        if isinstance(block, Paragraph):
            para_content = process_paragraph_with_math(
                block, image_dir, image_id_counter, relationship_map)

            # 处理列表 - 增强有序列表处理
            if block.style.name.startswith('List'):
                # 提取列表信息
                start_num = para_content.pop() if len(para_content) > 3 else 1
                num_format = para_content.pop() if len(para_content) > 2 else "decimal"
                list_type = para_content.pop() if len(para_content) > 1 else "ul"
                list_item = para_content[0]  # 第一个元素是列表项

                # 如果当前不在列表中，或者列表类型发生变化
                if not in_list or current_list_type != list_type:
                    # 关闭上一个列表（如果有）
                    if in_list:
                        html_content.append(f'</{current_list_type}>')

                    # 开始新列表
                    if list_type == "ol":
                        # 设置列表CSS类
                        list_class = f' class="{num_format}"' if num_format else ''
                        # 设置起始序号
                        start_attr = f' start="{start_num}"' if start_num > 1 else ''
                        html_content.append(
                            f'<{list_type}{list_class}{start_attr}>')
                        current_list_start = start_num
                        list_start_set = True
                    else:
                        html_content.append(f'<{list_type}>')

                    in_list = True
                    current_list_type = list_type
                    current_list_format = num_format

                # 添加列表项
                html_content.append(list_item)
            else:
                # 非列表段落
                if in_list:
                    # 关闭当前列表
                    html_content.append(f'</{current_list_type}>')
                    in_list = False
                    current_list_type = None
                    current_list_format = None
                    list_start_set = False

                # 添加普通段落内容
                html_content.extend(para_content)

        elif isinstance(block, Table):
            if in_list:
                # 表格前关闭列表
                html_content.append(f'</{current_list_type}>')
                in_list = False
                current_list_type = None
                current_list_format = None
                list_start_set = False

            html_table = table_to_html(block)
            if html_table:
                html_content.append(html_table)

    # 关闭任何未关闭的列表
    if in_list:
        html_content.append(f'</{current_list_type}>')

    # 读取自定义CSS或使用默认CSS
    css_content = DEFAULT_CSS
    if css_file and os.path.exists(css_file):
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()

    # 创建完整的HTML文档
    html_body = '\n'.join(html_content)
    full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{os.path.basename(docx_path)} - Converted Document</title>
    <style>
        {css_content}
    </style>
    <!-- MathJax 支持数学公式渲染 -->
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</head>
<body>
    {html_body}
</body>
</html>"""

    # 后处理1：去除特定条件下段落的段首空格
    full_html = remove_leading_space_after_math(full_html)

    # 后处理2：去除所有斜体标签
    full_html = remove_italic_tags(full_html)

    # 写入HTML文件 - 确保UTF-8编码
    try:
        with open(output_html_path, 'w', encoding='utf-8') as f:
            f.write(full_html)
    except UnicodeEncodeError:
        with open(output_html_path, 'w', encoding='utf-8', errors='xmlcharrefreplace') as f:
            f.write(full_html)


def main():
    """命令行入口函数"""
    parser = argparse.ArgumentParser(
        description='将DOCX文件转换为HTML格式，支持数学公式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            使用示例：
            python docx2html.py document.docx
            python docx2html.py document.docx -o output.html -i my_images
            python docx2html.py document.docx -c custom.css
        """
    )
    parser.add_argument('docx_file', help='输入的DOCX文件路径')
    parser.add_argument('-o', '--output', help='输出的HTML文件路径（可选）')
    parser.add_argument('-i', '--image_dir',
                        default='images', help='图像保存目录（默认：images）')
    parser.add_argument('-c', '--css', help='自定义CSS文件路径（可选）')

    args = parser.parse_args()

    docx_path = args.docx_file
    output_path = args.output if args.output else os.path.splitext(docx_path)[
        0] + '.html'

    docx_to_html(docx_path, output_path, args.image_dir, args.css)
    print(f"转换完成! HTML文件已保存至: {output_path}")


if __name__ == "__main__":
    main()
