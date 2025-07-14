"""
数据分析API路由
提供数据分析和可视化支持功能
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from ..tools.logger import get_logger
from ..api.document import document_storage
from ..api.task import task_storage

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

def find_evaluation_result_for_document(document_id: str) -> Optional[Dict[str, Any]]:
    """
    查找文档的评估结果

    Args:
        document_id: 文档ID

    Returns:
        Optional[Dict[str, Any]]: 评估结果，如果没有找到则返回None
    """
    for task_info in task_storage.values():
        if task_info.get('status') == 'completed':
            result = task_info.get('result', {})
            # 这里需要根据实际的结果结构来判断是否匹配文档ID
            # 暂时返回第一个完成的评估结果
            if result:
                return result
    return None

@router.get("/summary/{document_id}", response_model=AnalysisResponse)
async def get_analysis_summary(document_id: str):
    """
    获取文档分析摘要

    Args:
        document_id: 文档ID

    Returns:
        AnalysisResponse: 分析摘要
    """
    try:
        logger.info(f"获取文档分析摘要: {document_id}")

        # 检查文档是否存在
        if document_id not in document_storage:
            raise HTTPException(status_code=404, detail="文档不存在")

        document_info = document_storage[document_id]

        # 获取文档基本信息
        pkl_data = document_info.get('pkl_data', {})
        chapters = pkl_data.get('chapters', [])

        # 计算基本统计信息
        total_chapters = len(chapters)
        total_words = sum(len(chapter.get('content', '')) for chapter in chapters)
        total_images = sum(len(chapter.get('images', [])) for chapter in chapters)

        # 查找评估结果
        evaluation_result = find_evaluation_result_for_document(document_id)

        # 计算平均分数
        average_score = 0
        if evaluation_result:
            dimensions = evaluation_result.get('dimensions', {})
            if dimensions:
                scores = list(dimensions.values())
                average_score = sum(scores) / len(scores) if scores else 0

        summary_data = {
            'document_id': document_id,
            'filename': document_info.get('filename', ''),
            'total_chapters': total_chapters,
            'total_words': total_words,
            'total_images': total_images,
            'average_score': round(average_score, 2),
            'has_evaluation': evaluation_result is not None,
            'processing_status': document_info.get('status', 'unknown')
        }

        return AnalysisResponse(
            success=True,
            message="分析摘要获取成功",
            data=summary_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分析摘要失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取分析摘要失败: {str(e)}")

@router.get("/chart/radar/{document_id}", response_model=ChartDataResponse)
async def get_radar_chart_data(document_id: str):
    """
    获取雷达图数据

    Args:
        document_id: 文档ID

    Returns:
        ChartDataResponse: 雷达图数据
    """
    try:
        logger.info(f"获取雷达图数据: {document_id}")

        # 检查文档是否存在
        if document_id not in document_storage:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 查找评估结果
        evaluation_result = find_evaluation_result_for_document(document_id)

        if not evaluation_result:
            # 如果没有评估结果，返回默认数据
            return ChartDataResponse(
                success=True,
                chart_type="radar",
                data={
                    'dimensions': ['创新性', '技术深度', '实验设计', '写作质量', '学术规范'],
                    'scores': [0, 0, 0, 0, 0]
                },
                options={
                    'title': '论文质量评估雷达图',
                    'max_score': 100,
                    'message': '暂无评估数据'
                }
            )

        # 提取维度分数
        dimensions_data = evaluation_result.get('dimensions', {})
        dimensions = ['创新性', '技术深度', '实验设计', '写作质量', '学术规范']
        scores = [
            dimensions_data.get('创新性', 0),
            dimensions_data.get('技术深度', 0),
            dimensions_data.get('实验设计', 0),
            dimensions_data.get('写作质量', 0),
            dimensions_data.get('学术规范', 0)
        ]

        return ChartDataResponse(
            success=True,
            chart_type="radar",
            data={
                'dimensions': dimensions,
                'scores': scores
            },
            options={
                'title': '论文质量评估雷达图',
                'max_score': 100,
                'overall_score': evaluation_result.get('overall_score', 0)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取雷达图数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取雷达图数据失败: {str(e)}")

@router.get("/chart/bar/{document_id}", response_model=ChartDataResponse)
async def get_bar_chart_data(document_id: str):
    """
    获取柱状图数据

    Args:
        document_id: 文档ID

    Returns:
        ChartDataResponse: 柱状图数据
    """
    try:
        logger.info(f"获取柱状图数据: {document_id}")

        # 检查文档是否存在
        if document_id not in document_storage:
            raise HTTPException(status_code=404, detail="文档不存在")

        document_info = document_storage[document_id]
        pkl_data = document_info.get('pkl_data', {})
        chapters = pkl_data.get('chapters', [])

        # 查找评估结果
        evaluation_result = find_evaluation_result_for_document(document_id)

        categories = []
        scores = []

        if evaluation_result and 'chapter_scores' in evaluation_result:
            # 使用实际的章节评分
            chapter_scores = evaluation_result.get('chapter_scores', [])
            for chapter_score in chapter_scores:
                categories.append(chapter_score.get('chapter', '未知章节'))
                scores.append(chapter_score.get('score', 0))
        else:
            # 使用章节名称和默认分数
            for i, chapter in enumerate(chapters):
                chapter_name = chapter.get('chapter_name', f'第{i+1}章')
                categories.append(chapter_name)
                scores.append(75)  # 默认分数

        # 如果没有章节数据，提供默认数据
        if not categories:
            categories = ['暂无章节数据']
            scores = [0]

        return ChartDataResponse(
            success=True,
            chart_type="bar",
            data={
                'categories': categories,
                'scores': scores
            },
            options={
                'title': '各章节评分对比',
                'y_axis_title': '评分',
                'x_axis_title': '章节',
                'has_evaluation': evaluation_result is not None
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取柱状图数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取柱状图数据失败: {str(e)}")

@router.get("/statistics/{document_id}")
async def get_document_statistics(document_id: str):
    """
    获取文档统计信息

    Args:
        document_id: 文档ID

    Returns:
        dict: 统计信息
    """
    try:
        logger.info(f"获取文档统计信息: {document_id}")

        # 检查文档是否存在
        if document_id not in document_storage:
            raise HTTPException(status_code=404, detail="文档不存在")

        document_info = document_storage[document_id]
        pkl_data = document_info.get('pkl_data', {})

        # 基本统计信息
        chapters = pkl_data.get('chapters', [])
        total_chapters = len(chapters)

        # 计算字数统计
        total_words = 0
        total_images = 0
        chapter_lengths = []

        for chapter in chapters:
            content = chapter.get('content', '')
            chapter_length = len(content.split())  # 简单的单词计数
            chapter_lengths.append(chapter_length)
            total_words += chapter_length
            total_images += len(chapter.get('images', []))

        average_chapter_length = total_words / total_chapters if total_chapters > 0 else 0

        # 查找评估信息
        evaluation_result = find_evaluation_result_for_document(document_id)
        evaluation_time = None
        model_used = None

        if evaluation_result:
            # 从任务存储中查找评估时间和使用的模型
            for task_info in task_storage.values():
                if task_info.get('result') == evaluation_result:
                    evaluation_time = task_info.get('updated_at')
                    # 模型信息可能需要从其他地方获取
                    break

        statistics = {
            'total_words': total_words,
            'total_chapters': total_chapters,
            'total_images': total_images,
            'average_chapter_length': round(average_chapter_length, 2),
            'longest_chapter': max(chapter_lengths) if chapter_lengths else 0,
            'shortest_chapter': min(chapter_lengths) if chapter_lengths else 0,
            'file_size': document_info.get('size', 0),
            'filename': document_info.get('filename', ''),
            'upload_time': document_info.get('created_at'),
            'processing_status': document_info.get('status', 'unknown'),
            'evaluation_time': evaluation_time,
            'model_used': model_used or 'unknown',
            'has_evaluation': evaluation_result is not None
        }

        return {
            'success': True,
            'document_id': document_id,
            'statistics': statistics
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取文档统计信息失败: {str(e)}")

@router.get("/export/{document_id}")
async def export_analysis_report(
    document_id: str,
    format: str = Query("json", description="导出格式: json, summary")
):
    """
    导出分析报告

    Args:
        document_id: 文档ID
        format: 导出格式 (json, summary)

    Returns:
        dict: 导出结果
    """
    try:
        logger.info(f"导出分析报告: {document_id}, 格式: {format}")

        # 检查文档是否存在
        if document_id not in document_storage:
            raise HTTPException(status_code=404, detail="文档不存在")

        document_info = document_storage[document_id]
        evaluation_result = find_evaluation_result_for_document(document_id)

        if format == "json":
            # 导出完整的JSON数据
            export_data = {
                'document_info': {
                    'id': document_id,
                    'filename': document_info.get('filename', ''),
                    'size': document_info.get('size', 0),
                    'status': document_info.get('status', 'unknown')
                },
                'evaluation_result': evaluation_result,
                'export_time': json.dumps(datetime.now().isoformat()),
                'format': 'json'
            }

            return {
                'success': True,
                'message': 'JSON格式报告导出成功',
                'document_id': document_id,
                'format': format,
                'data': export_data
            }

        elif format == "summary":
            # 导出摘要格式
            if not evaluation_result:
                summary_data = {
                    'document_id': document_id,
                    'filename': document_info.get('filename', ''),
                    'status': '未评估',
                    'message': '该文档尚未进行评估'
                }
            else:
                summary_data = {
                    'document_id': document_id,
                    'filename': document_info.get('filename', ''),
                    'overall_score': evaluation_result.get('overall_score', 0),
                    'dimensions': evaluation_result.get('dimensions', {}),
                    'summary': evaluation_result.get('summary', ''),
                    'strengths': evaluation_result.get('detailed_analysis', {}).get('strengths', []),
                    'weaknesses': evaluation_result.get('detailed_analysis', {}).get('weaknesses', []),
                    'suggestions': evaluation_result.get('detailed_analysis', {}).get('suggestions', [])
                }

            return {
                'success': True,
                'message': '摘要格式报告导出成功',
                'document_id': document_id,
                'format': format,
                'data': summary_data
            }

        else:
            raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出分析报告失败: {e}")
        raise HTTPException(status_code=500, detail=f"导出分析报告失败: {str(e)}")
