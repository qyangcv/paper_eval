"""
请求日志记录中间件
记录所有HTTP请求和响应的详细信息
"""

import time
import json
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..tools.logger import get_logger

logger = get_logger(__name__)

class LoggingMiddleware(BaseHTTPMiddleware):
    """请求日志记录中间件"""
    
    def __init__(self, app, log_requests: bool = True, log_responses: bool = True):
        """
        初始化日志中间件
        
        Args:
            app: FastAPI应用实例
            log_requests: 是否记录请求日志
            log_responses: 是否记录响应日志
        """
        super().__init__(app)
        self.log_requests = log_requests
        self.log_responses = log_responses
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        处理请求并记录日志
        
        Args:
            request: HTTP请求
            call_next: 下一个中间件或路由处理器
            
        Returns:
            Response: HTTP响应
        """
        start_time = time.time()
        
        # 记录请求信息
        if self.log_requests:
            await self._log_request(request)
        
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录响应信息
        if self.log_responses:
            await self._log_response(request, response, process_time)
        
        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    async def _log_request(self, request: Request):
        """
        记录请求日志
        
        Args:
            request: HTTP请求
        """
        try:
            # 获取客户端IP
            client_ip = self._get_client_ip(request)
            
            # 获取请求体（如果存在且不是文件上传）
            request_body = None
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    try:
                        body = await request.body()
                        if body:
                            request_body = json.loads(body.decode())
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        request_body = "<无法解析的请求体>"
                elif "multipart/form-data" in content_type:
                    request_body = "<文件上传请求>"
                elif "application/x-www-form-urlencoded" in content_type:
                    request_body = "<表单数据>"
            
            # 记录请求日志
            log_data = {
                "type": "request",
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                "client_ip": client_ip,
                "user_agent": request.headers.get("user-agent"),
                "body": request_body
            }
            
            logger.info(f"[IN] {request.method} {request.url.path} - {client_ip}")
            logger.debug(f"请求详情: {json.dumps(log_data, ensure_ascii=False, indent=2)}")
            
        except Exception as e:
            logger.error("记录请求日志失败: %s", str(e))
    
    async def _log_response(self, request: Request, response: Response, process_time: float):
        """
        记录响应日志
        
        Args:
            request: HTTP请求
            response: HTTP响应
            process_time: 处理时间
        """
        try:
            # 获取客户端IP
            client_ip = self._get_client_ip(request)
            
            # 记录响应日志
            log_data = {
                "type": "response",
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "process_time": round(process_time, 4),
                "client_ip": client_ip
            }
            
            # 根据状态码选择日志级别
            if response.status_code < 400:
                logger.info(
                    f"[OUT] {request.method} {request.url.path} - "
                    f"{response.status_code} - {process_time:.4f}s - {client_ip}"
                )
            elif response.status_code < 500:
                logger.warning(
                    f"[WARN] {request.method} {request.url.path} - "
                    f"{response.status_code} - {process_time:.4f}s - {client_ip}"
                )
            else:
                logger.error(
                    f"[ERROR] {request.method} {request.url.path} - "
                    f"{response.status_code} - {process_time:.4f}s - {client_ip}"
                )
            
            logger.debug(f"响应详情: {json.dumps(log_data, ensure_ascii=False, indent=2)}")
            
        except Exception as e:
            logger.error("记录响应日志失败: %s", str(e))
    
    def _get_client_ip(self, request: Request) -> str:
        """
        获取客户端真实IP地址
        
        Args:
            request: HTTP请求
            
        Returns:
            str: 客户端IP地址
        """
        # 尝试从各种头部获取真实IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        forwarded = request.headers.get("X-Forwarded")
        if forwarded:
            return forwarded
        
        # 如果都没有，使用客户端地址
        if request.client:
            return request.client.host
        
        return "unknown"
