import os
import cv2
import base64
import tempfile
import requests
import asyncio
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from loguru import logger
from PicImageSearch import Bing, Network
from PicImageSearch.model import BingResponse

# 配置
PROXIES = None
DEFAULT_THRESHOLD = 0.6
MAX_SEARCH_RESULTS = 10

def calculate_orb_similarity(image1_bytes: bytes, image2_bytes: bytes, threshold: float = 0.6) -> tuple[bool, float]:
    """
    计算两张图片的ORB特征相似度
    
    Args:
        image1_bytes: 第一张图片的字节数据
        image2_bytes: 第二张图片的字节数据  
        threshold: 相似度阈值
        
    Returns:
        tuple[bool, float]: (是否相似, 匹配度分数)
    """
    try:
        # 将字节数据转换为numpy数组
        nparr1 = np.frombuffer(image1_bytes, np.uint8)
        nparr2 = np.frombuffer(image2_bytes, np.uint8)
        
        # 解码图片
        img1 = cv2.imdecode(nparr1, cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imdecode(nparr2, cv2.IMREAD_GRAYSCALE)
        
        if img1 is None or img2 is None:
            return False, 0.0
            
        img1_pixels = img1.shape[0] * img1.shape[1]
        img2_pixels = img2.shape[0] * img2.shape[1]

        larger_image, smaller_image = (img1, img2) if img1_pixels > img2_pixels else (img2, img1)
        ratio = min(img1_pixels, img2_pixels) / max(img1_pixels, img2_pixels)

        # 创建ORB检测器
        orb_larger = cv2.ORB.create(nfeatures=1000)
        orb_smaller = cv2.ORB.create(nfeatures=int(500 * ratio))

        kp1, des1 = orb_larger.detectAndCompute(larger_image, None)  # type: ignore
        kp2, des2 = orb_smaller.detectAndCompute(smaller_image, None)  # type: ignore

        if des1 is None or des2 is None:
            return False, 0.0

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)

        # 计算匹配的特征点数量
        match_count = len(matches)

        # 计算原图和裁剪图像的特征点数量
        feature_count_img1 = len(kp1)
        feature_count_img2 = len(kp2)

        # 计算匹配点占特征点数量的比例
        match_ratio_img1 = match_count / feature_count_img1 if feature_count_img1 > 0 else 0
        match_ratio_img2 = match_count / feature_count_img2 if feature_count_img2 > 0 else 0

        # 取较高的匹配率作为相似度分数
        similarity_score = max(match_ratio_img1, match_ratio_img2)
        
        logger.debug(f"Feature points: img1={feature_count_img1}, img2={feature_count_img2}")
        logger.debug(f"Match ratios: img1={match_ratio_img1:.3f}, img2={match_ratio_img2:.3f}")
        logger.debug(f"Final similarity score: {similarity_score:.3f}")

        # 判断是否相似
        is_similar = similarity_score >= threshold
        return is_similar, similarity_score

    except Exception as e:
        logger.error(f"计算图片相似度失败: {e}")
        return False, 0.0

async def search_similar_images(image_bytes: bytes) -> List[Dict[str, Any]]:
    """
    使用Bing搜索相似图片
    
    Args:
        image_bytes: 图片字节数据
        
    Returns:
        List[Dict[str, Any]]: 搜索结果列表
    """
    try:
        # 保存临时图片文件
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_file.write(image_bytes)
            temp_file.flush()
            temp_file_path = temp_file.name

        try:
            # 使用异步Bing搜索
            async with Network(proxies=PROXIES) as client:
                bing = Bing(client=client)
                resp = await bing.search(file=temp_file_path)
                
                results = []
                
                # 处理包含该图片的页面
                if resp.pages_including:
                    for page_item in resp.pages_including:
                        if page_item.image_url:
                            results.append({
                                'name': page_item.name or 'Unknown',
                                'url': page_item.url,
                                'image_url': page_item.image_url,
                                'thumbnail': page_item.thumbnail,
                                'source': 'pages_including'
                            })
                
                # 处理视觉搜索结果
                if resp.visual_search:
                    for visual_item in resp.visual_search:
                        if visual_item.image_url:
                            results.append({
                                'name': visual_item.name or 'Unknown',
                                'url': visual_item.url,
                                'image_url': visual_item.image_url,
                                'thumbnail': visual_item.thumbnail,
                                'source': 'visual_search'
                            })
                
                # 限制结果数量
                return results[:MAX_SEARCH_RESULTS]
                
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_file_path)
            except:
                pass
                
    except Exception as e:
        logger.error(f"搜索相似图片失败: {e}")
        return []

def download_image(url: str, timeout: int = 10) -> bytes:
    """
    下载网络图片
    
    Args:
        url: 图片URL
        timeout: 超时时间
        
    Returns:
        bytes: 图片字节数据
    """
    try:
        response = requests.get(url, timeout=timeout, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        return response.content
    except Exception as e:
        logger.warning(f"下载图片失败 {url}: {e}")
        return b''

async def process_single_image(image_info: Dict[str, Any], threshold: float = DEFAULT_THRESHOLD) -> Dict[str, Any]:
    """
    处理单张图片的重复检测
    
    Args:
        image_info: 图片信息字典，包含image_id, image_data, image_type, image_title等
        threshold: 相似度阈值
        
    Returns:
        Dict[str, Any]: 处理结果，包含image_id, image_title, image_info, image_type, reused_link, reused_sim
    """
    try:
        image_id = image_info.get('image_id', 'unknown')
        image_data_base64 = image_info.get('image_data', '')
        image_type = image_info.get('image_type', 'png')
        image_title = image_info.get('image_title', image_id)  # 获取图片标题，如果没有则使用image_id
        
        logger.info(f"开始处理图片: {image_id} (标题: {image_title})")
        
        # 解码base64图片数据
        if not image_data_base64:
            logger.warning(f"图片 {image_id} 没有数据")
            return {
                'image_id': image_id,
                'image_title': image_title,
                'image_info': image_data_base64,
                'image_type': f'.{image_type}',
                'reused_link': [],
                'reused_sim': []
            }
            
        try:
            original_image_bytes = base64.b64decode(image_data_base64)
        except Exception as e:
            logger.error(f"解码图片 {image_id} 失败: {e}")
            return {
                'image_id': image_id,
                'image_title': image_title,
                'image_info': image_data_base64,
                'image_type': f'.{image_type}',
                'reused_link': [],
                'reused_sim': []
            }
        
        # 搜索相似图片
        search_results = await search_similar_images(original_image_bytes)
        
        if not search_results:
            logger.info(f"图片 {image_id} 未找到相似图片")
            return {
                'image_id': image_id,
                'image_title': image_title,
                'image_info': image_data_base64,
                'image_type': f'.{image_type}',
                'reused_link': [],
                'reused_sim': []
            }
        
        # 检查每个搜索结果的相似度
        reused_links = []
        reused_similarities = []
        
        for result in search_results:
            try:
                # 下载网络图片
                web_image_bytes = download_image(result['image_url'])
                if not web_image_bytes:
                    continue
                    
                # 计算相似度
                is_similar, similarity_score = calculate_orb_similarity(
                    original_image_bytes, web_image_bytes, threshold
                )
                
                if is_similar:
                    reused_links.append(result['url'])
                    reused_similarities.append(f"{similarity_score:.3f}")
                    logger.info(f"图片 {image_id} 找到相似图片: {result['url']} (相似度: {similarity_score:.3f})")
                    
            except Exception as e:
                logger.warning(f"处理搜索结果失败: {e}")
                continue
        
        return {
            'image_id': image_id,
            'image_title': image_title,
            'image_info': image_data_base64,
            'image_type': f'.{image_type}',
            'reused_link': reused_links,
            'reused_sim': reused_similarities
        }
        
    except Exception as e:
        logger.error(f"处理图片 {image_info.get('image_id', 'unknown')} 失败: {e}")
        return {
            'image_id': image_info.get('image_id', 'unknown'),
            'image_title': image_info.get('image_title', image_info.get('image_id', 'unknown')),
            'image_info': image_info.get('image_data', ''),
            'image_type': f'.{image_info.get("image_type", "png")}',
            'reused_link': [],
            'reused_sim': []
        }

async def eval(images_info: List[Dict[str, Any]], threshold: float = DEFAULT_THRESHOLD) -> str:
    """
    评估图片重复使用情况
    
    Args:
        images_info: 图片信息列表，每个元素包含image_id, image_data, image_type, image_title等
        threshold: 相似度阈值，默认0.6
        
    Returns:
        str: JSON格式的评估结果，包含总重复数量和详细信息
    """
    try:
        if not images_info:
            result = {
                "total_reused": 0,
                "detail": []
            }
            return str(result)
        
        logger.info(f"开始评估 {len(images_info)} 张图片的重复使用情况")
        
        # 并发处理所有图片（但限制并发数以避免过多请求）
        semaphore = asyncio.Semaphore(3)  # 最多同时处理3张图片
        
        async def process_with_semaphore(image_info):
            async with semaphore:
                return await process_single_image(image_info, threshold)
        
        # 处理所有图片
        tasks = [process_with_semaphore(img_info) for img_info in images_info]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 整理结果
        detail = []
        total_reused = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"处理第 {i+1} 张图片时发生异常: {result}")
                # 尝试从原始图片信息中获取标题
                original_image = images_info[i] if i < len(images_info) else {}
                image_id = original_image.get('image_id', f'img_{i+1}')
                image_title = original_image.get('image_title', image_id)
                
                # 添加错误的默认结果
                detail.append({
                    'image_id': image_id,
                    'image_title': image_title,
                    'image_info': '',
                    'image_type': '.png',
                    'reused_link': [],
                    'reused_sim': []
                })
            else:
                # result 是字典类型
                detail.append(result)
                if isinstance(result, dict) and result.get('reused_link', []):  # 如果找到了重复使用的链接
                    total_reused += 1
        
        final_result = {
            "total_reused": total_reused,
            "detail": detail
        }
        
        logger.info(f"图片重复评估完成: 总共检测 {len(images_info)} 张图片，发现 {total_reused} 张重复使用")
        
        import json
        return json.dumps(final_result, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"图片重复评估失败: {e}")
        # 返回错误结果
        error_result = {
            "total_reused": 0,
            "detail": [],
            "error": str(e)
        }
        import json
        return json.dumps(error_result, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    # 测试代码
    async def test():
        # 这里可以添加测试代码
        test_images = [
            {
                'image_id': 'test_img_1',
                'image_data': '',  # 这里应该是base64编码的图片数据
                'image_type': 'png'
            }
        ]
        result = await eval(test_images)
        print(result)
    
    # asyncio.run(test())
    print("图片重复检测模块已加载")
