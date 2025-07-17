"""
文档预览API路由
提供文档预览相关功能
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from typing import Dict, Any
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.logger import get_logger
from utils.redis_client import get_redis_manager

logger = get_logger(__name__)
router = APIRouter()

@router.get("/{task_id}/html")
async def get_preview_html(task_id: str):
    """
    获取文档预览数据

    Args:
        task_id: 任务ID

    Returns:
        dict: 文档预览数据
    """
    try:
        logger.info(f"获取任务 {task_id} 的预览数据")

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()

        # 检查文档是否存在
        document_info = await redis_mgr.get_document(task_id)
        if document_info is None:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 获取文档基本信息
        filename = document_info.get('filename', 'document.docx')

        # 检查是否有预生成的HTML文件
        html_file_path = document_info.get('html_file_path')
        html_content = None

        if html_file_path:
            # 首先尝试读取修复后的HTML文件
            from pathlib import Path
            original_path = Path(html_file_path)
            fixed_path = original_path.parent / "document_fixed.html"

            # 优先使用修复后的HTML文件
            html_path_to_use = fixed_path if fixed_path.exists() else original_path

            # 读取HTML文件内容
            try:
                with open(html_path_to_use, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                logger.info(f"成功读取HTML文件: {html_path_to_use}")

                # 处理HTML中的图片路径，确保前端能正确加载图片
                # 将相对路径的图片引用替换为API路径
                import re
                html_content = re.sub(
                    r'src="images/([^"]+)"',
                    f'src="/api/preview/{task_id}/image?path=images/\\1"',
                    html_content
                )

            except Exception as e:
                logger.warning(f"读取HTML文件失败: {e}")
                html_content = None

        # 如果没有HTML内容，生成默认内容
        if not html_content:
            html_content = f"""
            <!DOCTYPE html>
            <html lang="zh-CN">
            <head>
                <title>{filename}</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 800px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f8f9fa;
                    }}
                    .loading-container {{
                        text-align: center;
                        padding: 50px;
                        background: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .loading-title {{
                        color: #2c3e50;
                        margin-bottom: 20px;
                    }}
                    .loading-text {{
                        color: #7f8c8d;
                        font-size: 16px;
                    }}
                </style>
            </head>
            <body>
                <div class="loading-container">
                    <h2 class="loading-title">文档预览准备中</h2>
                    <p class="loading-text">HTML内容正在生成，请稍候...</p>
                </div>
            </body>
            </html>
            """

        # 提取目录信息
        toc_items = []

        # 方法1: 从pkl_data中提取目录信息
        pkl_data = document_info.get('pkl_data', {})
        chapters = pkl_data.get('chapters', [])

        if chapters:
            # 构建目录项
            for i, chapter in enumerate(chapters):
                chapter_name = chapter.get('chapter_name', f'第{i+1}章')
                # 判断章节级别（简单判断）
                level = 1
                if '.' in chapter_name:
                    level = chapter_name.count('.') + 1

                toc_items.append({
                    "text": chapter_name,
                    "level": level
                })

        # 方法2: 如果pkl_data中没有章节信息，尝试从HTML中提取标题
        elif html_content:
            import re
            # 提取HTML中的标题标签
            heading_pattern = r'<h([1-6])[^>]*>(.*?)</h[1-6]>'
            headings = re.findall(heading_pattern, html_content, re.IGNORECASE | re.DOTALL)

            for level_str, title in headings:
                level = int(level_str)
                # 清理HTML标签
                clean_title = re.sub(r'<[^>]+>', '', title).strip()
                if clean_title:
                    toc_items.append({
                        "text": clean_title,
                        "level": level
                    })

        # 如果仍然没有目录项，创建一个默认项
        if not toc_items:
            toc_items.append({
                "text": "文档内容",
                "level": 1
            })

        return {
            "filename": filename,
            "html_content": html_content,
            "toc_items": toc_items
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取预览数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取预览数据失败: {str(e)}")

@router.get("/{task_id}/image")
async def get_preview_image(task_id: str, path: str = Query(..., description="图片路径参数")):
    """
    获取文档中的图片资源

    Args:
        task_id: 任务ID
        path: 图片路径参数，如 images/image_1.png

    Returns:
        Response: 图片文件内容
    """
    try:
        logger.info(f"获取任务 {task_id} 的图片: {path}")

        # 获取Redis管理器
        redis_mgr = await get_redis_manager()

        # 检查文档是否存在
        document_info = await redis_mgr.get_document(task_id)
        if document_info is None:
            raise HTTPException(status_code=404, detail="文档不存在")

        # 首先尝试从预览目录中直接读取图片文件（docx2html生成的）
        from pathlib import Path
        preview_dir = Path("preview") / task_id
        image_file_path = preview_dir / path

        if image_file_path.exists():
            logger.info(f"从预览目录读取图片: {image_file_path}")
            try:
                with open(image_file_path, 'rb') as f:
                    image_data = f.read()

                # 根据文件扩展名确定MIME类型
                file_ext = image_file_path.suffix.lower()
                if file_ext == '.png':
                    media_type = 'image/png'
                elif file_ext in ['.jpg', '.jpeg']:
                    media_type = 'image/jpeg'
                elif file_ext == '.gif':
                    media_type = 'image/gif'
                elif file_ext == '.bmp':
                    media_type = 'image/bmp'
                else:
                    media_type = 'image/png'  # 默认

                return Response(content=image_data, media_type=media_type)

            except Exception as e:
                logger.error(f"读取预览目录图片失败: {e}")

        # 如果预览目录中没有找到，尝试从Redis中的图片数据获取
        images = document_info.get('images', [])
        logger.info(f"文档中共有 {len(images)} 张图片")

        # 从路径中提取图片ID或索引
        import re
        # 尝试从路径中提取图片编号
        match = re.search(r'image[_\-]?(\d+)', path)
        if match:
            requested_number = int(match.group(1))
            logger.info(f"请求图片编号: {requested_number}")

            # 尝试多种索引策略来找到正确的图片
            image_info = None
            image_index = None

            # 策略1: 直接使用编号作为1基索引 (image_1.png -> images[0])
            if 1 <= requested_number <= len(images):
                image_index = requested_number - 1
                image_info = images[image_index]
                logger.info(f"使用1基索引策略，索引: {image_index}")

            # 策略2: 如果策略1失败，尝试0基索引 (image_0.png -> images[0])
            elif image_info is None and 0 <= requested_number < len(images):
                image_index = requested_number
                image_info = images[image_index]
                logger.info(f"使用0基索引策略，索引: {image_index}")

            # 策略3: 通过image_id匹配
            elif image_info is None:
                for idx, img in enumerate(images):
                    img_id = img.get('image_id', '')
                    if img_id and str(requested_number) in img_id:
                        image_index = idx
                        image_info = img
                        logger.info(f"通过image_id匹配，索引: {image_index}")
                        break

            if image_info:
                logger.info(f"找到图片信息: {list(image_info.keys())}")

                # 获取图片数据
                image_data = image_info.get('image_data', '')
                image_type = image_info.get('image_type', 'png')

                if not image_data:
                    logger.warning(f"图片 {requested_number} 没有数据")
                    raise HTTPException(status_code=404, detail="图片数据不存在")

                # 解码base64图片数据
                import base64
                try:
                    image_bytes = base64.b64decode(image_data)
                    logger.info(f"成功解码图片数据，大小: {len(image_bytes)} bytes")
                except Exception as e:
                    logger.error(f"解码图片数据失败: {e}")
                    raise HTTPException(status_code=500, detail="图片数据解码失败")

                # 返回图片响应
                return Response(
                    content=image_bytes,
                    media_type=f"image/{image_type}",
                    headers={"Content-Disposition": f"inline; filename=image_{requested_number}.{image_type}"}
                )
            else:
                logger.warning(f"图片编号 {requested_number} 未找到，总数: {len(images)}")
                # 输出调试信息
                for idx, img in enumerate(images):
                    img_id = img.get('image_id', 'unknown')
                    logger.debug(f"图片 {idx}: image_id={img_id}")
        else:
            logger.warning(f"无法从路径中提取图片编号: {path}")

        # 如果没有找到对应的图片
        raise HTTPException(status_code=404, detail="图片不存在")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取图片失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取图片失败: {str(e)}")
