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
import re
import io
import tempfile
import os


sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.logger import get_logger
from utils.redis_client import get_redis_manager
from utils.task_storage import get_task_storage
from utils.async_tasks import get_task_manager
from api.eval_module import (
    soft_eval,
    hard_eval,
    img_eval,
    ref_eval
)
from tools.docx_tools.docx_analysis_functions import (
    get_basic_info as extract_basic_info,
    get_overall_stats as extract_overall_stats,
    get_chapter_stats as extract_chapter_stats,
    get_ref_stats as extract_ref_stats
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

        # 获取docx文件数据
        docx_data = document_info.get('content')
        if docx_data is None:
            raise HTTPException(status_code=404, detail="DOCX文件数据不存在")
        
        # 将bytes数据写入临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
            temp_file.write(docx_data)
            temp_file_path = temp_file.name
        
        try:
            # 使用docx_analysis_functions中的函数提取基础信息
            basic_info = extract_basic_info(temp_file_path)
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)
        
        return basic_info

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

        # 获取docx文件数据
        docx_data = document_info.get('content')
        if docx_data is None:
            raise HTTPException(status_code=404, detail="DOCX文件数据不存在")
        
        # 将bytes数据写入临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
            temp_file.write(docx_data)
            temp_file_path = temp_file.name
        
        try:
            # 使用docx_analysis_functions中的函数提取统计信息
            stats = extract_overall_stats(temp_file_path)
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)
        
        return stats

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

        # 获取docx文件数据
        docx_data = document_info.get('content')
        if docx_data is None:
            raise HTTPException(status_code=404, detail="DOCX文件数据不存在")
        
        # 将bytes数据写入临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
            temp_file.write(docx_data)
            temp_file_path = temp_file.name
        
        try:
            # 使用docx_analysis_functions中的函数提取章节统计信息
            stats = extract_chapter_stats(temp_file_path)
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)
        
        return stats

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

        # 获取docx文件数据
        docx_data = document_info.get('content')
        if docx_data is None:
            raise HTTPException(status_code=404, detail="DOCX文件数据不存在")
        
        # 将bytes数据写入临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as temp_file:
            temp_file.write(docx_data)
            temp_file_path = temp_file.name
        
        try:
            # 使用docx_analysis_functions中的函数提取参考文献统计信息
            stats = extract_ref_stats(temp_file_path)
        finally:
            # 清理临时文件
            os.unlink(temp_file_path)
        
        return stats

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

        # 检查文档是否已完成所有评估
        if document_info['status'] != 'completed':
            raise HTTPException(status_code=400, detail="文档尚未处理完成")

        # 直接调用软指标评估
        logger.info("开始软指标评估...")
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
        dict: 问题分析数据，合并hard_eval、img_eval、ref_eval三个模块的结果
    """
    try:
        logger.info(f"获取任务 {task_id} 的问题分析数据")

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()

        # 检查文档是否存在
        document_info = await redis_mgr.get_document(task_id)
        if document_info is None:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 检查文档是否已完成所有评估
        if document_info['status'] != 'completed':
            raise HTTPException(status_code=400, detail="文档尚未处理完成")

        # 优化：首先检查Redis中是否已有评估结果，避免重复评估
        logger.info(f"获取任务 {task_id} 的评估结果...")

        # 从Redis中获取已有的评估结果
        hard_result = document_info.get('hard_eval_result')
        img_result = document_info.get('img_eval_result')
        ref_result = document_info.get('ref_eval_result')

        # 只有当结果不存在时才调用评估模块
        if hard_result is None:
            logger.info(f"硬指标评估结果不存在，开始评估: {task_id}")
            hard_result = await hard_eval(task_id)
        else:
            logger.info(f"使用已有的硬指标评估结果: {task_id}")

        if img_result is None:
            logger.info(f"图片评估结果不存在，开始评估: {task_id}")
            img_result = await img_eval(task_id)
        else:
            logger.info(f"使用已有的图片评估结果: {task_id}")

        if ref_result is None:
            logger.info(f"参考文献评估结果不存在，开始评估: {task_id}")
            ref_result = await ref_eval(task_id)
        else:
            logger.info(f"使用已有的参考文献评估结果: {task_id}")
        
        # 解析结果，添加错误处理
        try:
            if isinstance(hard_result, str):
                hard_data = json.loads(hard_result)
            else:
                hard_data = hard_result
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"解析硬指标结果失败: {e}")
            hard_data = {
                "summary": {
                    "total_issues": 0,
                    "issue_types": [],
                    "severity_distribution": {"高": 0, "中": 0, "低": 0}
                },
                "by_chapter": {}
            }

        try:
            if isinstance(img_result, str):
                img_data = json.loads(img_result)
            else:
                img_data = img_result
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"解析图片分析结果失败: {e}")
            img_data = {
                "total_reused": 0,
                "detail": []
            }

        try:
            if isinstance(ref_result, str):
                ref_data = json.loads(ref_result)
            else:
                ref_data = ref_result
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"解析参考文献结果失败: {e}")
            ref_data = {
                "total_issues": 0,
                "detail": []
            }

        # 开始合并结果
        merged_result = {
            "summary": hard_data.get("summary", {
                "total_issues": 0,
                "issue_types": [],
                "severity_distribution": {"高": 0, "中": 0, "低": 0}
            }),
            "by_chapter": hard_data.get("by_chapter", {}).copy()
        }

        # 计算当前最大ID
        current_max_id = 0
        for chapter_issues in merged_result["by_chapter"].values():
            for issue in chapter_issues:
                try:
                    issue_id = int(issue.get("id", 0))
                    current_max_id = max(current_max_id, issue_id)
                except (ValueError, TypeError):
                    pass

        # 添加图片问题
        if img_data.get('total_reused', 0) > 0:
            if "图片" not in merged_result["by_chapter"]:
                merged_result["by_chapter"]["图片"] = []
            
            for img_detail in img_data.get('detail', []):
                # 检查是否有实际的重用链接和相似度
                reused_links = img_detail.get('reused_link', [])
                reused_sims = img_detail.get('reused_sim', [])
                
                # 如果没有重用链接或相似度，跳过这一项
                if not reused_links or not reused_sims:
                    continue
                
                current_max_id += 1
                
                # 构建相似度描述
                similarity_desc = []
                for i, link in enumerate(reused_links):
                    sim = reused_sims[i] if i < len(reused_sims) else "未知"
                    similarity_desc.append(f"与 '{link}' 相似度为 '{sim}'")
                
                detail_text = f"{img_detail.get('image_title', '')} 存在复用问题：{', '.join(similarity_desc)}"
                
                img_issue = {
                    "id": current_max_id,
                    "type": "",
                    "severity": "",
                    "sub_chapter": "",
                    "original_text": img_detail.get('image_title', ''),
                    "detail": detail_text,
                    "suggestion": "请避免直接使用论文、博客或其他出版物中的图片"
                }
                merged_result["by_chapter"]["图片"].append(img_issue)

        # 添加参考文献问题
        # 始终创建参考文献字段，即使没有问题
        if "参考文献" not in merged_result["by_chapter"]:
            merged_result["by_chapter"]["参考文献"] = []
        
        if ref_data.get('total_issues', 0) > 0:
            for ref_detail in ref_data.get('detail', []):
                current_max_id += 1
                
                # 合并建议
                suggestions = ref_detail.get('suggestions', [])
                suggestion_text = " | ".join(suggestions) if suggestions else ""
                
                ref_issue = {
                    "id": current_max_id,
                    "type": "",
                    "severity": "",
                    "sub_chapter": "",
                    "original_text": ref_detail.get('original_text', ''),
                    "detail": "",
                    "suggestion": suggestion_text
                }
                merged_result["by_chapter"]["参考文献"].append(ref_issue)

        # 更新总问题数
        hard_issues = hard_data.get("summary", {}).get("total_issues", 0)
        ref_issues = ref_data.get("total_issues", 0)
        
        # 计算实际添加的图片问题数
        actual_img_issues = 0
        if "图片" in merged_result["by_chapter"]:
            actual_img_issues = len(merged_result["by_chapter"]["图片"])
        
        total_issues = hard_issues + actual_img_issues + ref_issues
        merged_result["summary"]["total_issues"] = total_issues

        return merged_result

    except Exception as e:
        logger.error(f"获取问题分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取问题分析失败: {str(e)}")

# 预览相关接口已移动到preview.py
# 图片评价接口已整合到issues接口中

@router.get("/{task_id}/evaluation-status")
async def get_evaluation_status(task_id: str):
    """
    获取评估任务状态

    Args:
        task_id: 任务ID

    Returns:
        dict: 评估状态信息
    """
    try:
        logger.info(f"获取任务 {task_id} 的评估状态")

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()

        # 检查文档是否存在
        document_info = await redis_mgr.get_document(task_id)
        if document_info is None:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 获取任务管理器
        from utils.async_tasks import get_task_manager
        task_manager = await get_task_manager()

        # 检查评估状态
        hard_eval_completed = document_info.get('hard_eval_result') is not None
        soft_eval_completed = document_info.get('soft_eval_result') is not None
        img_eval_completed = True  # 图片评估已禁用，视为已完成
        ref_eval_completed = document_info.get('ref_eval_result') is not None

        has_errors = (
            document_info.get('hard_eval_error') is not None or
            document_info.get('soft_eval_error') is not None or
            document_info.get('img_eval_error') is not None or
            document_info.get('ref_eval_error') is not None
        )

        background_task_running = task_manager.is_task_running(task_id)

        # 检查是否所有评估都已完成
        all_evaluations_completed = hard_eval_completed and soft_eval_completed and img_eval_completed and ref_eval_completed

        # 确定消息
        if all_evaluations_completed and not background_task_running:
            message = "所有评估已完成"
        elif background_task_running:
            message = "正在进行后台分析评估，预计需要5-7分钟..."
        elif has_errors:
            message = "部分评估出现错误，请检查日志"
        else:
            message = "评估尚未开始或未完成"

        status = {
            "hard_eval_completed": hard_eval_completed,
            "soft_eval_completed": soft_eval_completed,
            "img_eval_completed": img_eval_completed,
            "ref_eval_completed": ref_eval_completed,
            "background_task_running": background_task_running,
            "has_errors": has_errors,
            "message": message,
            "progress": document_info.get('progress', 0.0)
        }

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取评估状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取评估状态失败: {str(e)}")
