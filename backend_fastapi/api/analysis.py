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

class Issue(BaseModel):
    id: str
    type: str
    severity: str
    sub_chapter: str
    original_text: Optional[str] = None
    detail: str
    suggestion: str

class SearchOptions(BaseModel):
    min_similarity: float = 0.4
    context_window: int = 100

class FindOriginalTextRequest(BaseModel):
    issue: Issue
    search_options: Optional[SearchOptions] = None

class PositionInfo(BaseModel):
    chapter_title: Optional[str] = None
    paragraph_index: Optional[int] = None
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None

class FindOriginalTextResponseData(BaseModel):
    original_text: str
    similarity: float
    chapter_name: Optional[str] = None
    context_before: Optional[str] = None
    context_after: Optional[str] = None
    full_context: Optional[str] = None
    position_info: Optional[PositionInfo] = None

class FindOriginalTextResponse(BaseModel):
    success: bool
    message: str
    data: Optional[FindOriginalTextResponseData] = None

from fastapi import Depends

async def get_completed_document_info(task_id: str) -> Dict[str, Any]:
    """
    FastAPI 依赖项：获取已完成文档的信息。
    如果文档不存在或未完成，则抛出 HTTPException。
    """
    redis_mgr = await get_redis_manager()
    document_info = await redis_mgr.get_document(task_id)

    if document_info is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    if document_info.get('status') != 'completed':
        raise HTTPException(status_code=400, detail="文档尚未处理完成")

    return document_info


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
async def get_basic_info(task_id: str, document_info: Dict[str, Any] = Depends(get_completed_document_info)):
    """
    获取论文基础信息

    Args:
        task_id: 任务ID
        document_info: 依赖注入的文档信息

    Returns:
        dict: 论文基础信息
    """
    try:
        logger.info(f"获取任务 {task_id} 的基础信息")

        basic_info_result = document_info.get('basic_info_result')
        if basic_info_result is None:
            raise HTTPException(status_code=404, detail="基础信息尚未生成或不存在")

        # 解析结果，添加错误处理
        try:
            if isinstance(basic_info_result, str):
                basic_info_data = json.loads(basic_info_result)
            else:
                basic_info_data = basic_info_result
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"解析基础信息结果失败: {e}")
            raise HTTPException(status_code=500, detail=f"基础信息结果解析失败: {str(e)}")

        return basic_info_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取基础信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取基础信息失败: {str(e)}")

# 统计概览接口
@router.get("/{task_id}/overall-stats")
async def get_overall_stats(task_id: str, document_info: Dict[str, Any] = Depends(get_completed_document_info)):
    """
    获取整体统计数据

    Args:
        task_id: 任务ID
        document_info: 依赖注入的文档信息

    Returns:
        dict: 整体统计数据
    """
    try:
        logger.info(f"获取任务 {task_id} 的整体统计数据")

        overall_stats_result = document_info.get('overall_stats_result')
        if overall_stats_result is None:
            raise HTTPException(status_code=404, detail="整体统计数据尚未生成或不存在")

        # 解析结果，添加错误处理
        try:
            if isinstance(overall_stats_result, str):
                overall_stats_data = json.loads(overall_stats_result)
            else:
                overall_stats_data = overall_stats_result
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"解析整体统计结果失败: {e}")
            raise HTTPException(status_code=500, detail=f"整体统计结果解析失败: {str(e)}")

        return overall_stats_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取整体统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取整体统计数据失败: {str(e)}")

# 章节统计接口
@router.get("/{task_id}/chapter-stats")
async def get_chapter_stats(task_id: str, document_info: Dict[str, Any] = Depends(get_completed_document_info)):
    """
    获取章节详细统计（用于折线图）

    Args:
        task_id: 任务ID
        document_info: 依赖注入的文档信息

    Returns:
        dict: 章节统计数据
    """
    try:
        logger.info(f"获取任务 {task_id} 的章节统计数据")

        chapter_stats_result = document_info.get('chapter_stats_result')
        if chapter_stats_result is None:
            raise HTTPException(status_code=404, detail="章节统计数据尚未生成或不存在")

        # 解析结果，添加错误处理
        try:
            if isinstance(chapter_stats_result, str):
                chapter_stats_data = json.loads(chapter_stats_result)
            else:
                chapter_stats_data = chapter_stats_result
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"解析章节统计结果失败: {e}")
            raise HTTPException(status_code=500, detail=f"章节统计结果解析失败: {str(e)}")

        return chapter_stats_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取章节统计数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取章节统计数据失败: {str(e)}")

@router.get("/{task_id}/reference-stats")
async def get_ref_stats(task_id: str, document_info: Dict[str, Any] = Depends(get_completed_document_info)):
    """
    获取参考文献统计（用于饼图）

    Args:
        task_id: 任务ID
        document_info: 依赖注入的文档信息

    Returns:
        dict: 参考文献统计数据
    """
    try:
        logger.info(f"获取任务 {task_id} 的参考文献统计")

        ref_stats_result = document_info.get('ref_stats_result')
        if ref_stats_result is None:
            raise HTTPException(status_code=404, detail="参考文献统计数据尚未生成或不存在")

        # 解析结果，添加错误处理
        try:
            if isinstance(ref_stats_result, str):
                ref_stats_data = json.loads(ref_stats_result)
            else:
                ref_stats_data = ref_stats_result
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"解析参考文献统计结果失败: {e}")
            raise HTTPException(status_code=500, detail=f"参考文献统计结果解析失败: {str(e)}")

        return ref_stats_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取参考文献统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取参考文献统计失败: {str(e)}")

@router.get("/{task_id}/evaluation")
async def get_soft_eval(task_id: str, document_info: Dict[str, Any] = Depends(get_completed_document_info)):
    """
    获取软指标评估数据

    Args:
        task_id: 任务ID
        document_info: 依赖注入的文档信息

    Returns:
        dict: 软指标评估数据
    """
    try:
        logger.info(f"获取任务 {task_id} 的软指标评估数据")

        soft_result = document_info.get('soft_eval_result')
        if soft_result is None:
            raise HTTPException(status_code=404, detail="软指标评估结果尚未生成或不存在")

        # 解析结果，添加错误处理
        try:
            if isinstance(soft_result, str):
                soft_data = json.loads(soft_result)
            else:
                soft_data = soft_result
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"解析软指标结果失败: {e}")
            raise HTTPException(status_code=500, detail=f"软指标结果解析失败: {str(e)}")

        return soft_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取软指标评估数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取软指标评估数据失败: {str(e)}")

async def _merge_evaluation_results(hard_data: Dict[str, Any], img_data: Dict[str, Any], ref_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并硬指标、图片和参考文献评估结果

    Args:
        hard_data: 硬指标评估数据
        img_data: 图片评估数据
        ref_data: 参考文献评估数据

    Returns:
        Dict[str, Any]: 合并后的问题分析数据
    """
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
                issue_id_str = issue.get("id", "0")
                issue_id = int(issue_id_str)
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
                "id": str(current_max_id),
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
                "id": str(current_max_id),
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

@router.get("/{task_id}/issues")
async def get_hard_eval(task_id: str, document_info: Dict[str, Any] = Depends(get_completed_document_info)):
    """
    获取问题分析数据（用于环形图和问题列表）

    Args:
        task_id: 任务ID
        document_info: 依赖注入的文档信息

    Returns:
        dict: 问题分析数据，合并hard_eval、img_eval、ref_eval三个模块的结果
    """
    try:
        logger.info(f"获取任务 {task_id} 的问题分析数据")

        # 从Redis中获取已有的评估结果
        hard_result = document_info.get('hard_eval_result')
        img_result = document_info.get('img_eval_result')
        ref_result = document_info.get('ref_eval_result')

        if hard_result is None:
            raise HTTPException(status_code=404, detail="硬指标评估结果尚未生成或不存在")
        if img_result is None:
            raise HTTPException(status_code=404, detail="图片评估结果尚未生成或不存在")
        if ref_result is None:
            raise HTTPException(status_code=404, detail="参考文献评估结果尚未生成或不存在")
        
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

        # 调用辅助函数合并结果
        merged_result = await _merge_evaluation_results(hard_data, img_data, ref_data)

        return merged_result

    except Exception as e:
        logger.error(f"获取问题分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取问题分析失败: {str(e)}")

# 预览相关接口已移动到preview.py
# 图片评价接口已整合到issues接口中

@router.post("/{task_id}/find-original-text", response_model=FindOriginalTextResponse)
async def find_original_text(task_id: str, request: FindOriginalTextRequest):
    """
    在文档内容中查找问题的原文，支持模糊匹配。

    Args:
        task_id: 任务ID
        request: 包含问题信息和搜索选项的请求体

    Returns:
        FindOriginalTextResponse: 查找结果，包含匹配到的原文、相似度、上下文等
    """
    try:
        logger.info(f"开始为任务 {task_id} 查找原文")

        redis_mgr = await get_redis_manager()
        document_info = await redis_mgr.get_document(task_id)

        if document_info is None:
            raise HTTPException(status_code=404, detail="文档不存在")
        if document_info.get('status') != 'completed' and document_info.get('status') != 'processed':
            raise HTTPException(status_code=400, detail="文档尚未处理完成或处理失败")

        md_content = document_info.get('md_content')
        if not md_content:
            raise HTTPException(status_code=404, detail="文档Markdown内容不存在，无法进行原文查找")

        issue = request.issue
        search_options = request.search_options or SearchOptions()

        # 提取查询文本
        query_text = _extract_query_from_issue(issue)
        if not query_text:
            return FindOriginalTextResponse(success=False, message="无法从问题中提取查询文本")

        # 执行模糊匹配
        match_result = _find_best_match_in_document(query_text, md_content, search_options.min_similarity, search_options.context_window)

        if match_result:
            # 尝试获取更精确的位置信息（例如段落索引、偏移量）
            position_info = _get_position_info(md_content, match_result['original_text'], match_result['start_offset'])
            
            return FindOriginalTextResponse(
                success=True,
                message="原文查找成功",
                data=FindOriginalTextResponseData(
                    original_text=match_result['original_text'],
                    similarity=match_result['similarity'],
                    chapter_name=issue.sub_chapter or issue.chapter, # 优先使用sub_chapter
                    context_before=match_result['context_before'],
                    context_after=match_result['context_after'],
                    full_context=match_result['full_context'],
                    position_info=position_info
                )
            )
        else:
            return FindOriginalTextResponse(success=False, message="未找到匹配的原文")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查找原文失败: {e}")
        raise HTTPException(status_code=500, detail=f"查找原文失败: {str(e)}")

# --- 模糊匹配辅助函数 (从前端JS翻译为Python) ---

def _extract_query_from_issue(issue: Issue) -> str:
    queries = []

    detail = issue.detail or ''
    if detail:
        quoted_text = _extract_quoted_text(detail)
        if quoted_text and len(quoted_text) > 3:
            queries.append(quoted_text)
        
        clean_detail = re.sub(r'建议|应该|需要|可以|问题|错误|不当|不合适', '', detail)
        phrases = [p.strip() for p in re.split(r'[，。；！？\s]+', clean_detail) if len(p.strip()) > 5]
        queries.extend(phrases[:3])

    suggestion = issue.suggestion or ''
    if suggestion:
        quoted_text = _extract_quoted_text(suggestion)
        if quoted_text and len(quoted_text) > 3:
            queries.append(quoted_text)
        
        clean_suggestion = re.sub(r'建议|应该|需要|可以|改为|修改为|替换为', '', suggestion)
        phrases = [p.strip() for p in re.split(r'[，。；！？\s]+', clean_suggestion) if len(p.strip()) > 5]
        queries.extend(phrases[:2])

    if issue.original_text and issue.original_text.strip():
        queries.insert(0, issue.original_text.strip())

    if issue.type and len(issue.type) > 2:
        queries.append(issue.type)

    valid_queries = [q for q in queries if q and len(q) > 3]
    if not valid_queries:
        return ""

    return max(valid_queries, key=len)

def _extract_quoted_text(text: str) -> str:
    patterns = [
        r'"([^"]+)"',  # 中文双引号
        r'\'([^\']+)\'',  # 中文单引号
        r'"([^"]+)"',  # 英文双引号
        r'\'([^\']+)\'',  # 英文单引号
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            longest = max(matches, key=len)
            return longest.strip()
    return ""

def _calculate_levenshtein_similarity(s1: str, s2: str) -> float:
    if not s1 or not s2:
        return 0.0
    
    len1 = len(s1)
    len2 = len(s2)

    if len1 == 0:
        return 1.0 if len2 == 0 else 0.0
    if len2 == 0:
        return 0.0

    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            matrix[i][j] = min(
                matrix[i - 1][j] + 1,      # deletion
                matrix[i][j - 1] + 1,      # insertion
                matrix[i - 1][j - 1] + cost  # substitution
            )
    
    max_len = max(len1, len2)
    return (max_len - matrix[len1][len2]) / max_len

def _calculate_jaccard_similarity(s1: str, s2: str) -> float:
    if not s1 or not s2:
        return 0.0
    set1 = set(s1)
    set2 = set(s2)
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

def _calculate_cosine_similarity(s1: str, s2: str) -> float:
    if not s1 or not s2:
        return 0.0

    def get_char_freq(s: str) -> Dict[str, int]:
        freq = {}
        for char in s:
            freq[char] = freq.get(char, 0) + 1
        return freq

    freq1 = get_char_freq(s1)
    freq2 = get_char_freq(s2)

    all_chars = set(freq1.keys()).union(set(freq2.keys()))

    vec1 = [freq1.get(char, 0) for char in all_chars]
    vec2 = [freq2.get(char, 0) for char in all_chars]

    dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
    magnitude1 = (sum(v * v for v in vec1))**0.5
    magnitude2 = (sum(v * v for v in vec2))**0.5

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0
    return dot_product / (magnitude1 * magnitude2)

def _calculate_fuzzy_similarity(s1: str, s2: str) -> float:
    if not s1 or not s2:
        return 0.0
    clean1 = re.sub(r'[^\w\u4e00-\u9fff]', '', s1).lower()
    clean2 = re.sub(r'[^\w\u4e00-\u9fff]', '', s2).lower()
    return _calculate_levenshtein_similarity(clean1, clean2)

def _calculate_combined_similarity(s1: str, s2: str, weights: Optional[Dict[str, float]] = None) -> float:
    if weights is None:
        weights = {
            "levenshtein": 0.3,
            "jaccard": 0.2,
            "cosine": 0.3,
            "fuzzy": 0.2
        }
    
    similarities = {
        "levenshtein": _calculate_levenshtein_similarity(s1, s2),
        "jaccard": _calculate_jaccard_similarity(s1, s2),
        "cosine": _calculate_cosine_similarity(s1, s2),
        "fuzzy": _calculate_fuzzy_similarity(s1, s2)
    }

    total_weight = sum(weights.values())
    if total_weight == 0:
        return 0.0
    
    weighted_sum = sum(similarities[method] * weights.get(method, 0) for method in similarities)
    return weighted_sum / total_weight

def _apply_length_penalty(similarity: float, s1: str, s2: str, penalty_factor: float = 0.1) -> float:
    len1 = len(s1)
    len2 = len(s2)
    if len1 == 0 or len2 == 0:
        return 0.0
    length_ratio = min(len1, len2) / max(len1, len2)
    penalty = (1 - length_ratio) * penalty_factor
    adjusted_similarity = similarity * (1 - penalty)
    return max(0.0, adjusted_similarity)

def _split_text_into_segments(text: str, segment_type: str = 'sentence') -> List[str]:
    if not text:
        return []
    
    if segment_type == 'sentence':
        sentences = [s.strip() for s in re.split(r'[。！？；：\n]', text) if len(s.strip()) > 3]
        if len(sentences) < 3:
            clauses = [s.strip() for s in re.split(r'[，、]', text) if len(s.strip()) > 5]
            return clauses if len(clauses) > len(sentences) else sentences
        return sentences
    elif segment_type == 'paragraph':
        return [p.strip() for p in re.split(r'\n\s*\n', text) if len(p.strip()) > 10]
    elif segment_type == 'window':
        text_length = len(text)
        window_size = min(100, max(30, text_length // 10))
        step = max(1, window_size // 3)
        segments = []
        for i in range(0, text_length - window_size + 1, step):
            segments.append(text[i:i + window_size])
        if text_length > window_size and (text_length - window_size) % step != 0:
            segments.append(text[text_length - window_size:])
        return [s for s in segments if len(s.strip()) > 10]
    return [text]

def _find_best_match_in_document(query_text: str, document_content: str, min_similarity: float = 0.3, context_window: int = 100) -> Optional[Dict[str, Any]]:
    if not query_text or not document_content:
        return None

    segment_types = ['sentence', 'paragraph', 'window']
    best_match = None
    best_similarity = 0.0

    for segment_type in segment_types:
        segments = _split_text_into_segments(document_content, segment_type)
        
        for segment in segments:
            if not segment.strip():
                continue
            
            similarity = _calculate_combined_similarity(query_text, segment)
            adjusted_similarity = _apply_length_penalty(similarity, query_text, segment, 0.05)

            effective_min_similarity = min_similarity * 0.7 if len(query_text) < 10 else min_similarity

            if adjusted_similarity >= effective_min_similarity:
                if adjusted_similarity > best_similarity:
                    best_similarity = adjusted_similarity
                    best_match = {
                        'original_text': segment,
                        'similarity': adjusted_similarity,
                        'segment_type_used': segment_type
                    }
    
    if best_match:
        matched_text = best_match['original_text']
        match_start = document_content.find(matched_text)

        if match_start != -1:
            context_start = max(0, match_start - context_window)
            context_end = min(len(document_content), match_start + len(matched_text) + context_window)

            best_match['context_before'] = document_content[context_start:match_start]
            best_match['context_after'] = document_content[match_start + len(matched_text):context_end]
            best_match['full_context'] = document_content[context_start:context_end]
            best_match['start_offset'] = match_start
            best_match['end_offset'] = match_start + len(matched_text)
    
    return best_match

def _get_position_info(md_content: str, matched_text: str, start_offset: int) -> Optional[PositionInfo]:
    # 这是一个简化的位置信息提取，实际可能需要更复杂的逻辑来解析Markdown结构
    # 例如，识别章节标题，然后计算段落索引和文本偏移量
    
    # 简单地查找匹配文本所在的行，并假设该行属于某个“段落”
    lines = md_content.split('\n')
    paragraph_index = -1
    current_offset = 0
    
    for i, line in enumerate(lines):
        if start_offset >= current_offset and start_offset < current_offset + len(line) + 1: # +1 for newline char
            paragraph_index = i
            break
        current_offset += len(line) + 1 # +1 for newline char
            
    if paragraph_index != -1:
        return PositionInfo(
            paragraph_index=paragraph_index,
            start_offset=start_offset - (current_offset - len(lines[paragraph_index]) - 1), # Offset within the line/paragraph
            end_offset=start_offset - (current_offset - len(lines[paragraph_index]) - 1) + len(matched_text)
        )
    return None

