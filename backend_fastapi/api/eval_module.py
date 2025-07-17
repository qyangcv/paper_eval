"""
论文处理API子模块，供合并使用
"""

import uuid
import asyncio
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.logger import get_logger
from pipeline.paper_evaluation import full_paper_evaluation
from utils.task_storage import get_task_storage
from utils.redis_client import get_redis_manager

from api.document import get_document_markdown, extract_references_from_markdown

from pipeline.hard_eval import eval as hard_criterial_eval
from pipeline.soft_eval import eval as soft_criterial_eval
from pipeline.reference_eval import eval as reference_eval
from pipeline.image_eval import eval as image_eval

logger = get_logger(__name__)
router = APIRouter()
    
async def hard_eval(document_id: str):
    """
    执行硬指标评价
    
    对指定文档进行硬指标评价，包括格式规范、字数统计、结构完整性等客观指标。
    首先检查Redis缓存，如果有缓存结果则直接返回，否则重新计算并缓存结果。
    
    Args:
        document_id (str): 文档唯一标识符
        
    Returns:
        str: JSON格式的硬指标评价结果
        
    Raises:
        HTTPException: 当文档不存在、内容为空或评价过程出错时抛出
    """
    try:
        logger.info(f"对文档 {document_id} 进行硬指标评价")

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()
        
        # 首先检查Redis中是否已有该文档的硬指标评价结果
        # 使用特定的key格式便于管理和查询
        key = f"paper_eval:hard:{document_id}"
        cached_result = await redis_mgr._client.get(key) if redis_mgr._client else None
        
        if cached_result:
            logger.info(f"从Redis缓存中获取文档 {document_id} 的硬指标评价结果")
            return json.loads(cached_result)

        # 如果缓存中没有，则重新计算
        # 从Redis获取文档的markdown内容
        md_content = await get_document_markdown(document_id)

        if md_content:
            # 执行硬指标分析
            # 调用pipeline中的硬指标评价函数
            response = hard_criterial_eval(md_content)

            # 如果response是JSON字符串，需要解析为字典
            if isinstance(response, str):
                try:
                    response = json.loads(response)
                except json.JSONDecodeError:
                    logger.error(f"硬指标评价结果JSON解析失败: {response}")
                    response = {
                        "summary": {"total_issues": 0, "issue_types": [], "severity_distribution": {"高": 0, "中": 0, "低": 0}},
                        "by_chapter": {}
                    }

            # 将结果存储到Redis，设置1小时过期时间
            # 缓存可以提高响应速度，避免重复计算
            try:
                response_json = json.dumps(response, ensure_ascii=False, default=str)
                if redis_mgr._client:
                    await redis_mgr._client.setex(key, 3600, response_json)  # 1小时过期
                    logger.info(f"硬指标评价结果已存储到Redis: {document_id}")
            except Exception as store_error:
                logger.warning(f"存储硬指标评价结果到Redis失败: {store_error}")

            return response
        else:
            raise ValueError("文档内容为空，无法进行硬指标评价")
            
    except Exception as e:
        logger.error(f"文档硬指标评价失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取问题分析失败: {str(e)}")


async def soft_eval(document_id: str):
    """
    执行软指标评价
    
    对指定文档进行软指标评价，包括内容质量、逻辑连贯性、创新性等主观指标。
    使用AI模型进行分析评价，结果会缓存在Redis中以提高效率。
    
    Args:
        document_id (str): 文档唯一标识符
        
    Returns:
        str: JSON格式的软指标评价结果
        
    Raises:
        HTTPException: 当文档不存在、内容为空或评价过程出错时抛出
    """
    try:
        logger.info(f"对文档 {document_id} 进行软指标评价")

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()
        
        # 首先检查Redis中是否已有该文档的软指标评价结果
        # 软指标评价通常较为耗时，缓存尤为重要
        key = f"paper_eval:soft:{document_id}"
        cached_result = await redis_mgr._client.get(key) if redis_mgr._client else None
        
        if cached_result:
            logger.info(f"从Redis缓存中获取文档 {document_id} 的软指标评价结果")
            return json.loads(cached_result)

        # 如果缓存中没有，则重新计算
        # 获取文档的markdown内容进行分析
        md_content = await get_document_markdown(document_id)

        if md_content:
            # 执行软指标分析
            # 调用pipeline中的软指标评价函数，通常涉及AI模型调用
            response = soft_criterial_eval(md_content)
            
            # 将结果存储到Redis，设置1小时过期时间
            # 软指标评价成本较高，缓存可以显著提升用户体验
            try:
                response_json = json.dumps(response, ensure_ascii=False, default=str)
                if redis_mgr._client:
                    await redis_mgr._client.setex(key, 3600, response_json)  # 1小时过期
                    logger.info(f"软指标评价结果已存储到Redis: {document_id}")
            except Exception as store_error:
                logger.warning(f"存储软指标评价结果到Redis失败: {store_error}")
            
            return response
        else:
            raise ValueError("文档内容为空，无法进行软指标评价")
            
    except Exception as e:
        logger.error(f"文档软指标评价失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取软指标评价失败: {str(e)}")
    

async def ref_eval(document_id: str):
    """
    执行参考文献评价
    
    对指定文档的参考文献进行格式规范性评价，检查引用格式是否符合学术标准。
    首先从Redis中获取已提取的参考文献，如果没有则从markdown内容中重新提取。
    
    Args:
        document_id (str): 文档唯一标识符
        
    Returns:
        str: JSON格式的参考文献评价结果，包含格式错误详情和修改建议
        
    Raises:
        HTTPException: 当文档不存在、内容为空或评价过程出错时抛出
    """
    try:
        logger.info(f"对文档 {document_id} 进行参考文献评价")

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()
        
        # 首先检查Redis中是否已有该文档的参考文献评价结果
        key = f"paper_eval:ref:{document_id}"
        cached_result = await redis_mgr._client.get(key) if redis_mgr._client else None
        
        if cached_result:
            logger.info(f"从Redis缓存中获取文档 {document_id} 的参考文献评价结果")
            return json.loads(cached_result)

        # 获取文档信息，提取参考文献
        document_info = await redis_mgr.get_document(document_id)
        if not document_info:
            raise ValueError("文档不存在")
        
        # 从Redis中获取参考文献列表
        # 参考文献在文档处理时已经提取并存储
        references = document_info.get('references', [])
        
        if not references:
            # 如果Redis中没有参考文献，尝试从markdown内容中提取
            # 这是一个fallback机制，确保系统的鲁棒性
            md_content = document_info.get('md_content', '')
            if md_content:
                references = extract_references_from_markdown(md_content)
                # 更新文档信息中的参考文献，避免下次重复提取
                document_info['references'] = references
                await redis_mgr.store_document(document_id, document_info)
            else:
                raise ValueError("文档内容为空，无法进行参考文献评价")

        if references:
            # 执行参考文献格式评价
            # 使用AI模型检查引用格式的规范性
            response = reference_eval(references)
            
            # 将结果存储到Redis，设置1小时过期时间
            try:
                response_json = json.dumps(response, ensure_ascii=False, default=str)
                if redis_mgr._client:
                    await redis_mgr._client.setex(key, 3600, response_json)  # 1小时过期
                    logger.info(f"参考文献评价结果已存储到Redis: {document_id}")
            except Exception as store_error:
                logger.warning(f"存储参考文献评价结果到Redis失败: {store_error}")
            
            return response
        else:
            # 没有参考文献的情况
            # 返回标准化的结果格式，便于前端处理
            response = {
                "status": "success",
                "total_issues": 0,
                "detail": [],
                "message": "未找到参考文献"
            }
            return response
            
    except Exception as e:
        logger.error("文档参考文献评价失败: %s", str(e))
        raise HTTPException(status_code=500, detail=f"获取参考文献评价失败: {str(e)}")
    
async def img_eval(document_id: str):
    """
    执行图片重复检测评价
    
    对指定文档中的图片进行重复使用检测，通过图像相似度算法和网络搜索
    来判断图片是否可能来源于网络或其他文献，帮助检测学术不端行为。
    
    Args:
        document_id (str): 文档唯一标识符
        
    Returns:
        str: JSON格式的图片重复检测结果，包含每张图片的相似度分析和可能的原始来源
        
    Raises:
        HTTPException: 当文档不存在或检测过程出错时抛出
    """
    try:
        logger.info(f"对文档 {document_id} 进行图片重复检测")

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()
        
        # 首先检查Redis中是否已有该文档的图片评价结果
        # 图片检测涉及网络搜索和算法计算，缓存可以大幅提升效率
        key = f"paper_eval:img:{document_id}"
        cached_result = await redis_mgr._client.get(key) if redis_mgr._client else None
        
        if cached_result:
            logger.info(f"从Redis缓存中获取文档 {document_id} 的图片评价结果")
            return json.loads(cached_result)

        # 获取文档信息，提取图片信息
        document_info = await redis_mgr.get_document(document_id)
        if not document_info:
            raise ValueError("文档不存在")
        
        # 从Redis中获取图片列表
        # 图片信息在文档处理时已经提取，包含base64编码的图片数据和标题
        images = document_info.get('images', [])
        
        if not images:
            logger.warning(f"文档 {document_id} 中没有图片")
            # 没有图片的情况，返回标准化的空结果
            response = {
                "total_reused": 0,
                "detail": [],
                "message": "文档中没有图片"
            }
            return response

        logger.info(f"文档 {document_id} 中找到 {len(images)} 张图片，开始检测重复使用")
        
        # 执行图片重复检测
        # 使用计算机视觉算法和网络搜索来检测图片的重复使用情况
        # 包括ORB特征匹配、Bing图片搜索等技术
        response = await image_eval(images)
        
        # 将结果存储到Redis，设置1小时过期时间
        # 图片检测是计算密集型任务，缓存结果非常重要
        try:
            if redis_mgr._client:
                response_json = json.dumps(response, ensure_ascii=False, default=str) if isinstance(response, dict) else response
                await redis_mgr._client.setex(key, 3600, response_json)  # 1小时过期
                logger.info(f"图片评价结果已存储到Redis: {document_id}")
        except Exception as store_error:
            logger.warning(f"存储图片评价结果到Redis失败: {store_error}")

        # 确保返回的是字典格式
        if isinstance(response, str):
            try:
                return json.loads(response)
            except:
                return {"total_reused": 0, "detail": [], "message": "解析响应失败"}
        return response
            
    except Exception as e:
        logger.error(f"文档图片评价失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取图片评价失败: {str(e)}")


