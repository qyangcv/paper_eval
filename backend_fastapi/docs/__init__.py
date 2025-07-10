"""
API文档模块
提供API文档生成和配置功能

包含以下功能：
- OpenAPI配置
- API文档自定义
- 示例数据生成
"""

from .openapi_config import get_openapi_config, customize_openapi
from .examples import API_EXAMPLES

__all__ = ['get_openapi_config', 'customize_openapi', 'API_EXAMPLES']
