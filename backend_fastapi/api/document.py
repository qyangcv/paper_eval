"""
文档处理API路由
提供文档上传、转换、预处理等功能
"""

import os
import sys
import uuid
import logging
import base64
import tempfile
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from typing import Dict, Any, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.data_config import FILE_CONFIG
from tools.docx_tools.docx2md import convert_docx_bytes_to_md
from tools.docx_tools.md2pkl import convert_md_content_to_pkl_data
from tools.docx_tools.pkl_analyse import analyze_pkl_structure, get_document_summary
from tools.logger import get_logger
from utils.redis_client import get_redis_manager

logger = get_logger(__name__)
router = APIRouter()

# 响应模型
class DocumentUploadResponse(BaseModel):
    """文档上传响应模型"""
    success: bool
    message: str
    document_id: Optional[str] = None
    file_info: Optional[Dict[str, Any]] = None

class DocumentProcessResponse(BaseModel):
    """文档处理响应模型"""
    success: bool
    message: str
    document_id: str
    markdown_content: Optional[str] = None
    images: Optional[list] = None
    references: Optional[List[str]] = None
    structure: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None

class DocumentPreviewResponse(BaseModel):
    """文档预览响应模型"""
    success: bool
    message: str
    document_id: str
    content: Optional[str] = None
    images: Optional[list] = None
    references: Optional[List[str]] = None
    chapters: Optional[list] = None

# Redis存储（替代内存存储）
# document_storage = {}  # 已弃用，使用Redis存储

def validate_file(file: UploadFile) -> tuple[bool, str]:
    """
    验证上传的文件
    
    Args:
        file: 上传的文件
        
    Returns:
        tuple[bool, str]: (是否有效, 错误信息)
    """
    # 检查文件扩展名
    if not file.filename:
        return False, "文件名不能为空"
    
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in FILE_CONFIG['allowed_extensions']:
        return False, f"不支持的文件格式: {file_ext}。支持的格式: {', '.join(FILE_CONFIG['allowed_extensions'])}"
    
    # 检查文件大小（如果可以获取）
    if hasattr(file, 'size') and file.size:
        if file.size > FILE_CONFIG['max_file_size']:
            return False, f"文件大小超过限制: {file.size} > {FILE_CONFIG['max_file_size']}"
    
    return True, ""

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    上传文档文件
    
    Args:
        file: 上传的文档文件
        
    Returns:
        DocumentUploadResponse: 上传结果
    """
    try:
        logger.info(f"开始上传文档: {file.filename}")
        
        # 验证文件
        is_valid, error_msg = validate_file(file)
        if not is_valid:
            logger.warning(f"文件验证失败: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)
        
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 再次检查文件大小
        if file_size > FILE_CONFIG['max_file_size']:
            raise HTTPException(
                status_code=413, 
                detail=f"文件大小超过限制: {file_size} > {FILE_CONFIG['max_file_size']}"
            )
        
        # 生成文档ID
        document_id = str(uuid.uuid4())
        
        # 存储文档信息
        document_info = {
            'id': document_id,
            'filename': file.filename,
            'content_type': file.content_type,
            'size': file_size,
            'content': file_content,
            'status': 'uploaded'
        }
        
        # 使用Redis存储文档信息
        redis_mgr = await get_redis_manager()
        if not await redis_mgr.store_document(document_id, document_info):
            raise HTTPException(status_code=500, detail="文档存储失败")
        
        logger.info(f"文档上传成功: {file.filename}, ID: {document_id}")
        
        return DocumentUploadResponse(
            success=True,
            message="文档上传成功",
            document_id=document_id,
            file_info={
                'filename': file.filename,
                'size': file_size,
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"文档上传失败: {str(e)}")

@router.post("/process/{document_id}", response_model=DocumentProcessResponse)
async def process_document(document_id: str):
    """
    处理已上传的文档，转换为结构化数据
    
    Args:
        document_id: 文档ID
        
    Returns:
        DocumentProcessResponse: 处理结果
    """
    try:
        logger.info(f"开始处理文档: {document_id}")
        
        # 获取Redis管理器
        redis_mgr = await get_redis_manager()
        
        # 检查文档是否存在
        document_info = await redis_mgr.get_document(document_id)
        if document_info is None:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 检查文档状态
        if document_info['status'] == 'processing':
            raise HTTPException(status_code=409, detail="文档正在处理中")
        
        # 更新状态
        document_info['status'] = 'processing'
        await redis_mgr.store_document(document_id, document_info)
        
        # 转换为Markdown
        logger.info(f"转换文档为Markdown: {document_id}")
        md_content = convert_docx_bytes_to_md(document_info['content'])
        
        # 提取图片信息
        logger.info(f"提取文档图片: {document_id}")
        images = extract_images_from_docx(document_info['content'])
        logger.info(f"提取到 {len(images)} 张图片")
        
        # 提取参考文献
        logger.info(f"提取参考文献: {document_id}")
        references = extract_references_from_markdown(md_content)
        
        # 转换为结构化数据
        logger.info(f"转换为结构化数据: {document_id}")
        pkl_data = convert_md_content_to_pkl_data(md_content)
        
        # 保存处理结果到文档信息
        document_info['md_content'] = md_content
        document_info['images'] = images
        document_info['references'] = references
        document_info['pkl_data'] = pkl_data
        document_info['status'] = 'processed'
        
        # 分析文档结构
        # 创建临时文件用于分析
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as temp_file:
            import pickle
            pickle.dump(pkl_data, temp_file)
            temp_file.flush()
            
            try:
                structure = analyze_pkl_structure(temp_file.name)
                summary = get_document_summary(temp_file.name)
            finally:
                os.unlink(temp_file.name)
        
        document_info['structure'] = structure
        document_info['summary'] = summary
        
        # 保存到Redis
        await redis_mgr.store_document(document_id, document_info)
        
        logger.info(f"文档处理完成: {document_id}")
        
        return DocumentProcessResponse(
            success=True,
            message="文档处理完成",
            document_id=document_id,
            markdown_content=md_content,
            images=images,
            references=references,
            structure=structure,
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档处理失败: {e}")
        # 更新状态为失败
        try:
            redis_mgr = await get_redis_manager()
            document_info = await redis_mgr.get_document(document_id)
            if document_info:
                document_info['status'] = 'failed'
                document_info['error'] = str(e)
                await redis_mgr.store_document(document_id, document_info)
        except Exception as redis_error:
            logger.error(f"更新文档失败状态失败: {redis_error}")
        raise HTTPException(status_code=500, detail=f"文档处理失败: {str(e)}")

@router.get("/preview/{document_id}", response_model=DocumentPreviewResponse)
async def preview_document(document_id: str):
    """
    预览文档内容
    
    Args:
        document_id: 文档ID
        
    Returns:
        DocumentPreviewResponse: 预览结果
    """
    try:
        logger.info(f"预览文档: {document_id}")
        
        # 获取Redis管理器
        redis_mgr = await get_redis_manager()
        
        # 检查文档是否存在
        document_info = await redis_mgr.get_document(document_id)
        if document_info is None:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 检查文档是否已处理
        if document_info['status'] != 'processed':
            raise HTTPException(status_code=400, detail="文档尚未处理完成")
        
        # 获取markdown内容和图片
        md_content = document_info.get('md_content', '')
        images = document_info.get('images', [])
        references = document_info.get('references', [])
        
        # 获取章节信息
        pkl_data = document_info.get('pkl_data', {})
        chapters = pkl_data.get('chapters', [])
        
        # 格式化章节信息用于预览
        chapter_list = []
        for i, chapter in enumerate(chapters):
            chapter_list.append({
                'index': i,
                'name': chapter.get('chapter_name', f'第{i+1}章'),
                'content_length': len(chapter.get('content', '')),
                'image_count': len(chapter.get('images', []))
            })
        
        return DocumentPreviewResponse(
            success=True,
            message="文档预览获取成功",
            document_id=document_id,
            content=md_content,
            images=images,
            references=references,
            chapters=chapter_list
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档预览失败: {e}")
        raise HTTPException(status_code=500, detail=f"文档预览失败: {str(e)}")

@router.get("/status/{document_id}")
async def get_document_status(document_id: str):
    """
    获取文档处理状态
    
    Args:
        document_id: 文档ID
        
    Returns:
        dict: 文档状态信息
    """
    try:
        # 获取Redis管理器
        redis_mgr = await get_redis_manager()
        
        # 检查文档是否存在
        document_info = await redis_mgr.get_document(document_id)
        if document_info is None:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        return {
            'success': True,
            'document_id': document_id,
            'status': document_info['status'],
            'filename': document_info['filename'],
            'size': document_info['size'],
            'has_markdown': 'md_content' in document_info,
            'has_pkl_data': 'pkl_data' in document_info,
            'image_count': len(document_info.get('images', [])),
            'chapter_count': len(document_info.get('pkl_data', {}).get('chapters', [])),
            'error': document_info.get('error')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档状态失败: {str(e)}")

@router.delete("/delete/{document_id}")
async def delete_document(document_id: str):
    """
    删除文档
    
    Args:
        document_id: 文档ID
        
    Returns:
        dict: 删除结果
    """
    try:
        # 获取Redis管理器
        redis_mgr = await get_redis_manager()
        
        # 检查文档是否存在并删除
        if not await redis_mgr.document_exists(document_id):
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 删除文档
        if not await redis_mgr.delete_document(document_id):
            raise HTTPException(status_code=500, detail="文档删除失败")
        
        logger.info(f"文档删除成功: {document_id}")
        
        return {
            'success': True,
            'message': '文档删除成功',
            'document_id': document_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档删除失败: {e}")
        raise HTTPException(status_code=500, detail=f"文档删除失败: {str(e)}")

async def get_document_markdown(document_id: str) -> Optional[str]:
    """
    从Redis中获取指定文档的markdown内容
    
    Args:
        document_id: 文档ID
        
    Returns:
        Optional[str]: markdown内容，如果文档不存在或未处理则返回None
    """
    try:
        logger.info(f"获取文档 {document_id} 的Markdown内容")
        # 获取Redis管理器
        redis_mgr = await get_redis_manager()
        
        # 获取文档信息
        document_info = await redis_mgr.get_document(document_id)
        if document_info is None:
            logger.warning(f"文档不存在: {document_id}")
            return None
        
        # 检查文档是否已处理
        if document_info['status'] != 'processed':
            logger.warning(f"文档尚未处理完成: {document_id}, status: {document_info['status']}")
            return None
        
        # 返回markdown内容
        md_content = document_info.get('md_content', '')
        if not md_content:
            logger.warning(f"文档没有Markdown内容: {document_id}")
            return None
        logger.info(f"成功获取文档markdown内容: {document_id}, 长度: {len(md_content)}")
        return md_content
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取Markdown内容失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取Markdown内容失败: {str(e)}")

def extract_references_from_markdown(md_content: str) -> List[str]:
    """
    从Markdown内容中提取参考文献
    
    Args:
        md_content: Markdown内容
        
    Returns:
        List[str]: 参考文献列表，每条参考文献删除换行符
    """
    references = []
    
    # 查找参考文献章节的开始位置
    ref_pattern = r'#\s*参考文献'
    ref_match = re.search(ref_pattern, md_content, re.IGNORECASE)
    
    if not ref_match:
        logger.warning("未找到参考文献章节")
        return references
    
    # 获取参考文献章节开始位置
    ref_start = ref_match.end()
    
    # 查找下一个章节（如致谢、附录等）的开始位置作为结束位置
    # 匹配以#开头的章节标题
    next_section_pattern = r'\n#\s+(?!参考文献)'
    next_section_match = re.search(next_section_pattern, md_content[ref_start:], re.IGNORECASE)
    
    if next_section_match:
        ref_end = ref_start + next_section_match.start()
        ref_content = md_content[ref_start:ref_end]
    else:
        # 如果没有找到下一个章节，则参考文献内容到文档结尾
        ref_content = md_content[ref_start:]
    
    # 提取每条参考文献
    # 匹配形如 [1] 或 [1] 开头的行
    ref_item_pattern = r'\[(\d+)\]\s*(.+?)(?=\n\[\d+\]|\n#|\Z)'
    ref_matches = re.findall(ref_item_pattern, ref_content, re.DOTALL)
    
    for ref_num, ref_text in ref_matches:
        # 删除换行符和多余的空白字符
        clean_ref = re.sub(r'\s+', ' ', ref_text.strip())
        if clean_ref:
            references.append(f"[{ref_num}] {clean_ref}")
    
    logger.info(f"提取到 {len(references)} 条参考文献")
    return references


def extract_images_from_docx(docx_bytes: bytes) -> List[Dict[str, Any]]:
    """
    从DOCX文件中提取图片及其标题
    
    Args:
        docx_bytes: DOCX文件的字节数据
        
    Returns:
        List[Dict[str, Any]]: 图片信息列表，包含image_id、image_data、image_type、image_title等
    """
    try:
        from docx import Document
        from docx.shared import Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from io import BytesIO
        
        # 使用临时文件处理docx
        with tempfile.NamedTemporaryFile(suffix='.docx') as temp_file:
            temp_file.write(docx_bytes)
            temp_file.flush()
            
            doc = Document(temp_file.name)
            images = []
            
            # 先构建图片ID到文件名的映射
            image_rels = {}
            for rel in doc.part.rels.values():
                if "image" in rel.target_ref:
                    image_rels[rel.target_ref] = rel.target_part.blob
            
            # 遍历文档段落，查找图片和对应的标题
            for para_idx, paragraph in enumerate(doc.paragraphs):
                # 检查段落中是否包含图片
                for run in paragraph.runs:
                    # 检查run中是否有图片
                    for drawing in run.element.xpath('.//w:drawing'):
                        # 查找图片引用
                        for blip in drawing.xpath('.//a:blip'):
                            embed_id = blip.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
                            if embed_id:
                                # 查找对应的图片数据
                                rel = doc.part.rels.get(embed_id)
                                if rel and "image" in rel.target_ref:
                                    try:
                                        # 获取图片数据
                                        image_bytes = rel.target_part.blob
                                        image_ext = os.path.splitext(rel.target_ref)[-1] or '.png'
                                        
                                        # 生成图片ID
                                        image_id = f"img_{len(images) + 1}"
                                        
                                        # 将图片数据编码为base64
                                        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                                        
                                        # 查找图片标题
                                        image_title = find_image_title(doc, para_idx, image_id)
                                        
                                        images.append({
                                            'image_id': image_id,
                                            'image_data': image_base64,
                                            'image_type': image_ext.lstrip('.'),
                                            'image_title': image_title,
                                            'size': len(image_bytes)
                                        })
                                    except Exception as e:
                                        logger.warning(f"提取图片失败: {e}")
                                        continue
            
            # 如果没有找到图片，使用原来的方法作为备选
            if not images:
                logger.info("使用备选方法提取图片")
                for rel in doc.part.rels.values():
                    if "image" in rel.target_ref:
                        try:
                            # 获取图片数据
                            image_bytes = rel.target_part.blob
                            image_ext = os.path.splitext(rel.target_ref)[-1] or '.png'
                            
                            # 生成图片ID
                            image_id = f"img_{len(images) + 1}"
                            
                            # 将图片数据编码为base64
                            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                            
                            images.append({
                                'image_id': image_id,
                                'image_data': image_base64,
                                'image_type': image_ext.lstrip('.'),
                                'image_title': image_id,  # 使用image_id作为默认标题
                                'size': len(image_bytes)
                            })
                        except Exception as e:
                            logger.warning(f"提取图片失败: {e}")
                            continue
            
            return images
            
    except Exception as e:
        logger.error(f"提取图片时发生错误: {e}")
        return []


def find_image_title(doc, image_para_idx: int, default_title: str) -> str:
    """
    查找图片对应的标题
    
    Args:
        doc: Document对象
        image_para_idx: 包含图片的段落索引
        default_title: 默认标题（通常是image_id）
        
    Returns:
        str: 图片标题
    """
    try:
        # 图片标题通常在图片后的1-3个段落内
        # 检查图片段落后面的几个段落
        for offset in range(1, 4):  # 检查后面3个段落
            next_para_idx = image_para_idx + offset
            if next_para_idx >= len(doc.paragraphs):
                break
                
            para = doc.paragraphs[next_para_idx]
            para_text = para.text.strip()
            
            # 跳过空段落
            if not para_text:
                continue
            
            # 检查是否是图片标题的模式
            # 图片标题通常以"图"开头，包含数字和描述
            title_pattern = r'^图\s*[\d\-\.]+.*'
            if re.match(title_pattern, para_text):
                # 进一步检查段落格式是否符合图片标题特征
                if is_likely_image_title(para):
                    # 将空格替换为下划线
                    clean_title = para_text.replace(' ', '_')
                    logger.info(f"找到图片标题: {para_text} -> {clean_title}")
                    return clean_title
            
            # 如果遇到非空的普通段落（很长的文本），停止搜索
            if len(para_text) > 100:  # 假设图片标题不会超过100字符
                break
        
        # 也检查图片前面的段落（有些标题可能在图片上方）
        for offset in range(1, 3):  # 检查前面2个段落
            prev_para_idx = image_para_idx - offset
            if prev_para_idx < 0:
                break
                
            para = doc.paragraphs[prev_para_idx]
            para_text = para.text.strip()
            
            # 跳过空段落
            if not para_text:
                continue
            
            # 检查是否是图片标题的模式
            title_pattern = r'^图\s*[\d\-\.]+.*'
            if re.match(title_pattern, para_text):
                # 进一步检查段落格式是否符合图片标题特征
                if is_likely_image_title(para):
                    # 将空格替换为下划线
                    clean_title = para_text.replace(' ', '_')
                    logger.info(f"找到图片标题: {para_text} -> {clean_title}")
                    return clean_title
            
            # 如果遇到非空的普通段落，停止搜索
            if len(para_text) > 100:
                break
        
        logger.info(f"未找到图片标题，使用默认值: {default_title}")
        return default_title
        
    except Exception as e:
        logger.warning(f"查找图片标题时发生错误: {e}")
        return default_title


def is_likely_image_title(paragraph) -> bool:
    """
    判断段落是否可能是图片标题
    
    Args:
        paragraph: 段落对象
        
    Returns:
        bool: 是否可能是图片标题
    """
    try:
        # 检查段落对齐方式（图片标题通常居中）
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        if paragraph.alignment and paragraph.alignment == WD_ALIGN_PARAGRAPH.CENTER:
            return True
        
        # 检查字体样式（楷体等）
        for run in paragraph.runs:
            if run.font.name:
                font_name = run.font.name.lower()
                # 检查是否是楷体
                if '楷' in font_name or 'kai' in font_name:
                    return True
            
            # 检查是否是加粗或斜体（图片标题可能有特殊格式）
            if run.bold or run.italic:
                return True
        
        # 如果段落文本较短且包含"图"字，也认为可能是标题
        text = paragraph.text.strip()
        if len(text) < 50 and '图' in text:
            return True
        
        return False
        
    except Exception as e:
        logger.warning(f"检查段落格式时发生错误: {e}")
        return False
