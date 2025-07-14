"""
全局错误处理中间件
统一处理应用中的所有异常
"""

import traceback
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR

from ..tools.logger import get_logger

logger = get_logger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """全局错误处理中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并捕获异常
        
        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应
        """
        try:
            # 调用下一个中间件或路由处理器
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # FastAPI的HTTP异常，直接传递
            logger.warning(f"HTTP异常: {e.status_code} - {e.detail} - {request.url}")
            raise e
            
        except ValueError as e:
            # 值错误，通常是参数验证失败
            logger.error(f"参数错误: {str(e)} - {request.url}")
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "error": "参数错误",
                    "detail": str(e),
                    "error_type": "ValueError"
                }
            )
            
        except FileNotFoundError as e:
            # 文件未找到错误
            logger.error(f"文件未找到: {str(e)} - {request.url}")
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "error": "文件未找到",
                    "detail": str(e),
                    "error_type": "FileNotFoundError"
                }
            )
            
        except PermissionError as e:
            # 权限错误
            logger.error(f"权限错误: {str(e)} - {request.url}")
            return JSONResponse(
                status_code=403,
                content={
                    "success": False,
                    "error": "权限不足",
                    "detail": str(e),
                    "error_type": "PermissionError"
                }
            )
            
        except TimeoutError as e:
            # 超时错误
            logger.error(f"请求超时: {str(e)} - {request.url}")
            return JSONResponse(
                status_code=408,
                content={
                    "success": False,
                    "error": "请求超时",
                    "detail": str(e),
                    "error_type": "TimeoutError"
                }
            )
            
        except ConnectionError as e:
            # 连接错误
            logger.error(f"连接错误: {str(e)} - {request.url}")
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": "服务不可用",
                    "detail": str(e),
                    "error_type": "ConnectionError"
                }
            )
            
        except Exception as e:
            # 其他未预期的异常
            error_id = id(e)  # 生成错误ID用于追踪
            error_traceback = traceback.format_exc()
            
            logger.error(
                f"未处理的异常 [ID: {error_id}]: {str(e)} - {request.url}\n"
                f"Traceback:\n{error_traceback}"
            )
            
            # 在开发环境中返回详细错误信息
            from ..config.app_config import APP_CONFIG
            if APP_CONFIG.get('debug', False):
                return JSONResponse(
                    status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "success": False,
                        "error": "内部服务器错误",
                        "detail": str(e),
                        "error_type": type(e).__name__,
                        "error_id": error_id,
                        "traceback": error_traceback.split('\n') if APP_CONFIG.get('debug') else None
                    }
                )
            else:
                # 生产环境中返回通用错误信息
                return JSONResponse(
                    status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                    content={
                        "success": False,
                        "error": "内部服务器错误",
                        "detail": "服务器遇到了一个错误，请稍后重试",
                        "error_type": "InternalServerError",
                        "error_id": error_id
                    }
                )

def create_error_response(
    status_code: int,
    error: str,
    detail: str,
    error_type: str = "UnknownError"
) -> JSONResponse:
    """
    创建标准化的错误响应
    
    Args:
        status_code: HTTP状态码
        error: 错误消息
        detail: 错误详情
        error_type: 错误类型
        
    Returns:
        JSONResponse: 标准化的错误响应
    """
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": error,
            "detail": detail,
            "error_type": error_type
        }
    )
