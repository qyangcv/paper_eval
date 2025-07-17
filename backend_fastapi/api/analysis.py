"""
数据分析API路由
提供数据分析和可视化支持功能
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.logger import get_logger
from utils.redis_client import get_redis_manager
from utils.task_storage import get_task_storage
from api.eval_module import (
    hard_eval,
    soft_eval,
    img_eval
)

logger = get_logger(__name__)

router = APIRouter()

# 响应模型
class AnalysisResponse(BaseModel):
    """分析响应模型"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ChartDataResponse(BaseModel):
    """图表数据响应模型"""
    success: bool
    chart_type: str
    data: Dict[str, Any]
    options: Optional[Dict[str, Any]] = None

class IssuesResponse(BaseModel):
    """问题分析响应模型"""
    summary: Dict[str, Any]
    by_chapter: Dict[str, List[Dict[str, str]]]

async def find_evaluation_result_for_document(document_id: str) -> Optional[Dict[str, Any]]:
    """
    查找文档的评估结果

    Args:
        document_id: 文档ID

    Returns:
        Optional[Dict[str, Any]]: 评估结果，如果没有找到则返回None
    """
    try:
        storage = await get_task_storage()
        all_tasks = await storage.get_all_tasks()
        
        for task_info in all_tasks.values():
            if task_info.get('status') == 'completed':
                result = task_info.get('result', {})
                # 这里需要根据实际的结果结构来判断是否匹配文档ID
                # 暂时返回第一个完成的评估结果
                if result:
                    return result
        return None
    except Exception as e:
        logger.error(f"查找评估结果失败: {e}")
        return None

# 删除不在API需求中的summary路由

# 删除不在API需求中的radar图表路由

# 删除不在API需求中的bar图表路由

# 删除不在API需求中的statistics路由

# 删除不在API需求中的export路由
    
# 基础信息接口
@router.get("/{task_id}/basic-info")
async def get_basic_info(task_id: str):
    """
    获取论文基础信息

    Args:
        task_id: 任务ID

    Returns:
        dict: 论文基础信息
    """
    try:
        logger.info(f"获取任务 {task_id} 的基础信息")

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()

        # 检查文档是否存在
        document_info = await redis_mgr.get_document(task_id)
        if document_info is None:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 从pkl_data中提取基础信息
        pkl_data = document_info.get('pkl_data', {})

        # 提取标题、作者等信息
        title = pkl_data.get('title', '未知标题')
        author = pkl_data.get('author', '未知作者')
        school = pkl_data.get('school', '未知学院')
        advisor = pkl_data.get('advisor', '未知导师')
        keywords = pkl_data.get('keywords', [])

        return {
            "title": title,
            "author": author,
            "school": school,
            "advisor": advisor,
            "keywords": keywords
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取基础信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取基础信息失败: {str(e)}")

# 统计概览接口
@router.get("/{task_id}/overall-stats")
async def get_overall_stats(task_id: str):
    """
    获取整体统计数据

    Args:
        task_id: 任务ID

    Returns:
        dict: 整体统计数据
    """
    try:
        logger.info(f"获取任务 {task_id} 的整体统计数据")

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()

        # 检查文档是否存在
        document_info = await redis_mgr.get_document(task_id)
        if document_info is None:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 从pkl_data中提取统计信息
        pkl_data = document_info.get('pkl_data', {})
        chapters = pkl_data.get('chapters', [])

        # 计算统计数据
        total_words = sum(len(chapter.get('content', '').split()) for chapter in chapters)
        total_paragraphs = sum(len(chapter.get('content', '').split('\n\n')) for chapter in chapters)
        total_images = len(document_info.get('images', []))
        total_tables = sum(chapter.get('table_count', 0) for chapter in chapters)
        total_equations = sum(chapter.get('equation_count', 0) for chapter in chapters)

        return {
            "total_words": total_words,
            "total_equations": total_equations,
            "total_paragraphs": total_paragraphs,
            "total_images": total_images,
            "total_tables": total_tables
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取整体统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取整体统计数据失败: {str(e)}")

# 章节统计接口
@router.get("/{task_id}/chapter-stats")
async def get_chapter_stats(task_id: str):
    """
    获取章节详细统计（用于折线图）

    Args:
        task_id: 任务ID

    Returns:
        dict: 章节统计数据
    """
    try:
        logger.info(f"获取任务 {task_id} 的章节统计数据")

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()

        # 检查文档是否存在
        document_info = await redis_mgr.get_document(task_id)
        if document_info is None:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 从pkl_data中提取章节信息
        pkl_data = document_info.get('pkl_data', {})
        chapters = pkl_data.get('chapters', [])

        # 构建章节统计数据
        chapter_names = []
        word_counts = []
        equation_counts = []
        table_counts = []
        image_counts = []
        paragraph_counts = []

        for chapter in chapters:
            chapter_names.append(chapter.get('chapter_name', '未知章节'))
            content = chapter.get('content', '')
            word_counts.append(len(content.split()))
            equation_counts.append(chapter.get('equation_count', 0))
            table_counts.append(chapter.get('table_count', 0))
            image_counts.append(len(chapter.get('images', [])))
            paragraph_counts.append(len(content.split('\n\n')))

        return {
            "chapters": chapter_names,
            "word_counts": word_counts,
            "equation_counts": equation_counts,
            "table_counts": table_counts,
            "image_counts": image_counts,
            "paragraph_counts": paragraph_counts
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取章节统计数据失败: {str(e)}")

@router.get("/{task_id}/reference-stats")
async def get_ref_stats(task_id: str):
    """
    获取参考文献统计（用于饼图）

    Args:
        task_id: 任务ID

    Returns:
        dict: 参考文献统计数据
    """
    try:
        logger.info(f"获取任务 {task_id} 的参考文献统计")

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()

        # 检查文档是否存在
        document_info = await redis_mgr.get_document(task_id)
        if document_info is None:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 获取参考文献
        references = document_info.get('references', [])
        total_references = len(references)

        # 分析参考文献类型
        by_indicator = {
            "期刊论文[J]": 0,
            "会议论文[C]": 0,
            "学位论文[D]": 0,
            "技术报告[R]": 0,
            "其他": 0
        }

        by_lang = {
            "中文文献": 0,
            "英文文献": 0
        }

        recent_3y = 0
        current_year = datetime.now().year

        for ref in references:
            # 分析文献类型
            if '[J]' in ref:
                by_indicator["期刊论文[J]"] += 1
            elif '[C]' in ref:
                by_indicator["会议论文[C]"] += 1
            elif '[D]' in ref:
                by_indicator["学位论文[D]"] += 1
            elif '[R]' in ref:
                by_indicator["技术报告[R]"] += 1
            else:
                by_indicator["其他"] += 1

            # 分析语言（简单判断是否包含中文字符）
            if any('\u4e00' <= char <= '\u9fff' for char in ref):
                by_lang["中文文献"] += 1
            else:
                by_lang["英文文献"] += 1

            # 分析年份（简单提取4位数字作为年份）
            import re
            years = re.findall(r'\b(20\d{2})\b', ref)
            if years:
                year = int(years[-1])  # 取最后一个年份
                if current_year - year <= 3:
                    recent_3y += 1

        return {
            "total_references": total_references,
            "by_indicator": by_indicator,
            "by_lang": by_lang,
            "recent_3y": recent_3y
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取参考文献统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取参考文献统计失败: {str(e)}")

@router.get("/{task_id}/evaluation")
async def get_soft_eval(task_id: str):
    """
    获取软指标评估数据

    Args:
        task_id: 任务ID

    Returns:
        dict: 软指标评估数据
    """
    try:
        logger.info(f"获取任务 {task_id} 的软指标评估数据")

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()

        # 检查文档是否存在
        document_info = await redis_mgr.get_document(task_id)
        if document_info is None:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 检查文档是否已处理完成
        if document_info['status'] != 'processed':
            raise HTTPException(status_code=400, detail="文档尚未处理完成")

        # 从Redis中获取已经计算好的结果
        soft_result = document_info.get('soft_eval_result')

        # 如果没有预计算的结果，检查是否是无模型分析
        if soft_result is None:
            # 检查是否跳过了评估（无模型分析）
            if document_info.get('soft_eval_error') or 'hard_eval_result' not in document_info:
                logger.info("无模型分析，返回空的软指标结果")
                return {
                    "dimensions": [],
                    "overall_score": 0,
                    "summary": "无模型分析，未进行软指标评估"
                }

            logger.info("未找到预计算的软指标结果，重新计算...")
            soft_result = await soft_eval(task_id)

        return soft_result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取软指标评估数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取软指标评估数据失败: {str(e)}")

@router.get("/{task_id}/issues")
async def get_hard_eval(task_id: str):
    """
    获取问题分析数据（用于环形图和问题列表）

    Args:
        task_id: 任务ID

    Returns:
        dict: 问题分析数据，包含图片查重问题
    """
    try:
        logger.info(f"获取任务 {task_id} 的问题分析数据")

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()

        # 检查文档是否存在
        document_info = await redis_mgr.get_document(task_id)
        if document_info is None:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 检查文档是否已处理完成
        if document_info['status'] != 'processed':
            raise HTTPException(status_code=400, detail="文档尚未处理完成")

        # 从Redis中获取已经计算好的结果
        hard_result = document_info.get('hard_eval_result')
        img_result = document_info.get('img_eval_result')

        # 如果没有预计算的结果，检查是否是无模型分析
        if hard_result is None:
            # 检查是否跳过了评估（无模型分析）
            if document_info.get('hard_eval_error') or 'soft_eval_result' not in document_info:
                logger.info("无模型分析，返回空的硬指标结果")
                hard_result = {
                    "summary": {"total_issues": 0, "severity_distribution": {}},
                    "by_chapter": {}
                }
            else:
                logger.info("未找到预计算的硬指标结果，重新计算...")
                hard_result = await hard_eval(task_id)

        if img_result is None:
            logger.info("未找到预计算的图片分析结果，使用默认结果...")
            img_result = {
                "total_reused": 0,
                "detail": [],
                "message": "图片查重分析已跳过"
            }

        # 解析结果
        if isinstance(hard_result, str):
            hard_data = json.loads(hard_result)
        else:
            hard_data = hard_result

        if isinstance(img_result, str):
            img_data = json.loads(img_result)
        else:
            img_data = img_result

        # 将图片查重问题添加到issues中
        if img_data.get('total_reused', 0) > 0:
            # 为每个重复图片创建一个问题
            for img_detail in img_data.get('detail', []):
                # 添加到by_chapter中的适当位置
                chapter_name = "图片查重"  # 可以根据实际需要调整
                if chapter_name not in hard_data.get('by_chapter', {}):
                    hard_data['by_chapter'][chapter_name] = []

                # 创建图片查重问题
                img_issue = {
                    "id": f"img_{img_detail.get('image_id', 'unknown')}",
                    "type": "图片查重",
                    "severity": "高" if len(img_detail.get('reused_link', [])) > 0 else "中",
                    "sub_chapter": "图片使用",
                    "original_text": img_detail.get('image_title', ''),
                    "detail": f"图片可能存在重复使用，相似度: {', '.join(img_detail.get('reused_sim', []))}",
                    "suggestion": f"请检查图片来源: {', '.join(img_detail.get('reused_link', []))}"
                }
                hard_data['by_chapter'][chapter_name].append(img_issue)

            # 更新总问题数和类型
            hard_data['summary']['total_issues'] += img_data.get('total_reused', 0)
            if "图片查重" not in hard_data['summary']['issue_types']:
                hard_data['summary']['issue_types'].append("图片查重")

            # 更新严重程度分布
            severity_dist = hard_data['summary'].get('severity_distribution', {})
            severity_dist['高'] = severity_dist.get('高', 0) + img_data.get('total_reused', 0)

        return hard_data

    except Exception as e:
        logger.error(f"获取问题分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取问题分析失败: {str(e)}")

# 预览相关接口已移动到preview.py
# 图片评价接口已整合到issues接口中
