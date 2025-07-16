"""
数据验证工具
提供各种数据验证功能
"""

import os
import re
import mimetypes
from typing import Tuple, Optional, List
from fastapi import UploadFile, HTTPException

import sys
from pathlib import Path
# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.data_config import FILE_CONFIG
from models.model_manager import model_manager
from tools.logger import get_logger

logger = get_logger(__name__)

def validate_file_upload(file: UploadFile) -> Tuple[bool, Optional[str]]:
    """
    验证上传的文件
    
    Args:
        file: 上传的文件
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    try:
        # 检查文件名
        if not file.filename:
            return False, "文件名不能为空"
        
        # 检查文件扩展名
        file_ext = os.path.splitext(file.filename)[1].lower()
        allowed_extensions = FILE_CONFIG.get('allowed_extensions', {'.docx', '.doc'})
        
        if file_ext not in allowed_extensions:
            return False, f"不支持的文件格式: {file_ext}。支持的格式: {', '.join(allowed_extensions)}"
        
        # 检查MIME类型
        expected_mime_types = {
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword'
        }
        
        if file.content_type and file_ext in expected_mime_types:
            expected_mime = expected_mime_types[file_ext]
            if file.content_type != expected_mime:
                logger.warning(f"MIME类型不匹配: 期望 {expected_mime}, 实际 {file.content_type}")
                # 不直接拒绝，因为有些客户端可能发送错误的MIME类型
        
        # 检查文件名安全性
        if not is_safe_filename(file.filename):
            return False, "文件名包含不安全的字符"
        
        return True, None
        
    except Exception as e:
        logger.error(f"文件验证异常: {e}")
        return False, f"文件验证失败: {str(e)}"

def is_safe_filename(filename: str) -> bool:
    """
    检查文件名是否安全
    
    Args:
        filename: 文件名
        
    Returns:
        bool: 是否安全
    """
    # 检查是否包含路径遍历字符
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # 检查是否包含控制字符
    if any(ord(c) < 32 for c in filename):
        return False
    
    # 检查是否为保留文件名（Windows）
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in reserved_names:
        return False
    
    return True

def validate_file_size(file_size: int) -> Tuple[bool, Optional[str]]:
    """
    验证文件大小
    
    Args:
        file_size: 文件大小（字节）
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    max_size = FILE_CONFIG.get('max_file_size', 50 * 1024 * 1024)  # 默认50MB
    
    if file_size > max_size:
        return False, f"文件大小超过限制: {file_size} > {max_size} 字节"
    
    if file_size <= 0:
        return False, "文件大小无效"
    
    return True, None

def validate_model_name(model_name: str) -> Tuple[bool, Optional[str]]:
    """
    验证模型名称
    
    Args:
        model_name: 模型名称
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    try:
        # 检查模型名称是否为空
        if not model_name or not model_name.strip():
            return False, "模型名称不能为空"
        
        # 获取可用的模型列表
        available_models = model_manager.get_available_models()
        all_models = []
        for provider_models in available_models.values():
            all_models.extend(provider_models)
        
        # 检查模型是否在支持列表中
        if model_name not in all_models:
            return False, f"不支持的模型: {model_name}。支持的模型: {', '.join(all_models)}"
        
        # 检查模型配置是否有效
        if not model_manager.validate_model_config(model_name):
            return False, f"模型 {model_name} 配置无效或API密钥缺失"
        
        return True, None
        
    except Exception as e:
        logger.error(f"模型验证异常: {e}")
        return False, f"模型验证失败: {str(e)}"

def validate_document_id(document_id: str) -> Tuple[bool, Optional[str]]:
    """
    验证文档ID格式
    
    Args:
        document_id: 文档ID
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if not document_id or not document_id.strip():
        return False, "文档ID不能为空"
    
    # 检查UUID格式
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not re.match(uuid_pattern, document_id, re.IGNORECASE):
        return False, "文档ID格式无效"
    
    return True, None

def validate_task_id(task_id: str) -> Tuple[bool, Optional[str]]:
    """
    验证任务ID格式
    
    Args:
        task_id: 任务ID
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if not task_id or not task_id.strip():
        return False, "任务ID不能为空"
    
    # 检查UUID格式
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not re.match(uuid_pattern, task_id, re.IGNORECASE):
        return False, "任务ID格式无效"
    
    return True, None

def validate_pagination_params(limit: int, offset: int) -> Tuple[bool, Optional[str]]:
    """
    验证分页参数
    
    Args:
        limit: 限制数量
        offset: 偏移量
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if limit <= 0:
        return False, "limit参数必须大于0"
    
    if limit > 1000:
        return False, "limit参数不能超过1000"
    
    if offset < 0:
        return False, "offset参数不能小于0"
    
    return True, None

def sanitize_filename(filename: str) -> str:
    """
    清理文件名，移除不安全的字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    # 移除路径分隔符
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # 移除控制字符
    filename = ''.join(c for c in filename if ord(c) >= 32)
    
    # 移除多余的点
    filename = re.sub(r'\.+', '.', filename)
    
    # 确保不以点开头或结尾
    filename = filename.strip('.')
    
    # 如果文件名为空，使用默认名称
    if not filename:
        filename = "document"
    
    return filename

def validate_json_data(data: dict, required_fields: List[str]) -> Tuple[bool, Optional[str]]:
    """
    验证JSON数据是否包含必需字段
    
    Args:
        data: JSON数据
        required_fields: 必需字段列表
        
    Returns:
        Tuple[bool, Optional[str]]: (是否有效, 错误信息)
    """
    if not isinstance(data, dict):
        return False, "数据必须是JSON对象"
    
    missing_fields = []
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
    
    if missing_fields:
        return False, f"缺少必需字段: {', '.join(missing_fields)}"
    
    return True, None
