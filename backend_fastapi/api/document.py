"""
文档处理API路由
提供文档上传、转换、预处理等功能
"""

import os
import uuid
import tempfile
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..config.data_config import FILE_CONFIG
from ..tools.docx_tools.docx2md import convert_docx_bytes_to_md
from ..tools.docx_tools.md2pkl import convert_md_content_to_pkl_data
from ..tools.docx_tools.pkl_analyse import analyze_pkl_structure, get_document_summary
from ..tools.logger import get_logger

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
    structure: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None

class DocumentPreviewResponse(BaseModel):
    """文档预览响应模型"""
    success: bool
    message: str
    document_id: str
    content: Optional[str] = None
    chapters: Optional[list] = None

# 内存存储（生产环境应使用数据库或Redis）
document_storage = {}

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
        
        document_storage[document_id] = document_info
        
        logger.info(f"文档上传成功: {file.filename}, ID: {document_id}")
        
        return DocumentUploadResponse(
            success=True,
            message="文档上传成功",
            document_id=document_id,
            file_info={
                'filename': file.filename,
                'size': file_size,
                'content_type': file.content_type
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
        
        # 检查文档是否存在
        if document_id not in document_storage:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        document_info = document_storage[document_id]
        
        # 检查文档状态
        if document_info['status'] == 'processing':
            raise HTTPException(status_code=409, detail="文档正在处理中")
        
        # 更新状态
        document_info['status'] = 'processing'
        
        # 转换为Markdown
        logger.info(f"转换文档为Markdown: {document_id}")
        md_content = convert_docx_bytes_to_md(document_info['content'])
        
        # 转换为结构化数据
        logger.info(f"转换为结构化数据: {document_id}")
        pkl_data = convert_md_content_to_pkl_data(md_content)
        
        # 保存处理结果
        document_info['md_content'] = md_content
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
        
        logger.info(f"文档处理完成: {document_id}")
        
        return DocumentProcessResponse(
            success=True,
            message="文档处理完成",
            document_id=document_id,
            structure=structure,
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文档处理失败: {e}")
        # 更新状态为失败
        if document_id in document_storage:
            document_storage[document_id]['status'] = 'failed'
            document_storage[document_id]['error'] = str(e)
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
        
        # 检查文档是否存在
        if document_id not in document_storage:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        document_info = document_storage[document_id]
        
        # 检查文档是否已处理
        if document_info['status'] != 'processed':
            raise HTTPException(status_code=400, detail="文档尚未处理完成")
        
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
            content=document_info.get('md_content', ''),
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
        if document_id not in document_storage:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        document_info = document_storage[document_id]
        
        return {
            'success': True,
            'document_id': document_id,
            'status': document_info['status'],
            'filename': document_info['filename'],
            'size': document_info['size'],
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
        if document_id not in document_storage:
            raise HTTPException(status_code=404, detail="文档不存在")
        
        # 删除文档
        del document_storage[document_id]
        
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
