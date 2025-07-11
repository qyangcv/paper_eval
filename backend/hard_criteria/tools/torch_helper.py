"""
Helper functions to safely import and use PyTorch in a Streamlit environment.
This module provides safe imports that avoid issues with Streamlit's file watcher
which can crash when trying to inspect torch.classes.
"""

import importlib
import sys
import warnings
from typing import Any, Optional

# Dictionary to store lazily loaded modules
_cached_modules = {}


def lazy_import(module_name: str) -> Any:
    """Lazily import a module only when it's needed."""
    if module_name not in _cached_modules:
        _cached_modules[module_name] = importlib.import_module(module_name)
    return _cached_modules[module_name]


def get_torch():
    """Safely get the torch module."""
    return lazy_import("torch")


def get_transformers():
    """Safely get the transformers module."""
    return lazy_import("transformers")


def is_torch_available() -> bool:
    """Check if torch is available without importing it directly."""
    try:
        lazy_import("torch")
        return True
    except ImportError:
        return False


def is_cuda_available() -> bool:
    """Check if CUDA is available."""
    if not is_torch_available():
        return False
    return get_torch().cuda.is_available()


def get_device() -> str:
    """Get the appropriate device (cuda or cpu)."""
    if is_torch_available() and is_cuda_available():
        return "cuda"
    return "cpu"


def patch_streamlit_watcher():
    """
    Patch Streamlit's file watcher to safely handle torch modules.
    This prevents errors when Streamlit tries to inspect torch.classes.
    """
    try:
        # 导入Streamlit的文件监视器模块
        from streamlit.watcher import local_sources_watcher
        
        # 检查可用的函数并进行适当的补丁
        patched = False
        
        # 方法1: 尝试修补 get_module_paths 函数 (Streamlit 1.x)
        if hasattr(local_sources_watcher, "get_module_paths"):
            original_get_module_paths = local_sources_watcher.get_module_paths
            
            def safe_get_module_paths(module):
                """安全地获取模块路径，避开torch相关模块"""
                try:
                    if hasattr(module, "__name__") and (
                        module.__name__.startswith("torch") or 
                        "torch._classes" in str(module) or
                        module.__name__.startswith("transformers")
                    ):
                        return []
                    return original_get_module_paths(module)
                except Exception:
                    # 不输出警告，静默失败
                    return []
            
            local_sources_watcher.get_module_paths = safe_get_module_paths
            patched = True
        
        # 方法2: 尝试修补 extract_module_paths 函数 (Streamlit 1.x)
        if hasattr(local_sources_watcher, "extract_module_paths"):
            original_extract_module_paths = local_sources_watcher.extract_module_paths
            
            def safe_extract_module_paths(module):
                """安全地提取模块路径，避开torch相关模块"""
                try:
                    if hasattr(module, "__name__") and (
                        module.__name__.startswith("torch") or 
                        "torch._classes" in str(module) or
                        module.__name__.startswith("transformers")
                    ):
                        return []
                    return original_extract_module_paths(module)
                except Exception:
                    # 不输出警告，静默失败
                    return []
            
            local_sources_watcher.extract_module_paths = safe_extract_module_paths
            patched = True
        
        # 方法3: 尝试修补 extract_paths 函数 (可能存在于某些版本)
        if hasattr(local_sources_watcher, "extract_paths"):
            original_extract_paths = local_sources_watcher.extract_paths
            
            def safe_extract_paths(module):
                """安全地提取路径，避开torch相关模块"""
                try:
                    if hasattr(module, "__name__") and (
                        module.__name__.startswith("torch") or 
                        "torch._classes" in str(module) or
                        module.__name__.startswith("transformers")
                    ):
                        return []
                    return original_extract_paths(module)
                except Exception:
                    # 不输出警告，静默失败
                    return []
            
            local_sources_watcher.extract_paths = safe_extract_paths
            patched = True
            
        # 方法4: 修改 _extract_from_module 函数 (Streamlit 1.45+)
        if hasattr(local_sources_watcher, "_extract_from_module"):
            original_extract_from_module = local_sources_watcher._extract_from_module
            
            def safe_extract_from_module(module, extract_func):
                """安全地从模块提取信息，避开torch相关模块"""
                try:
                    if hasattr(module, "__name__") and (
                        module.__name__.startswith("torch") or 
                        "torch._classes" in str(module) or
                        module.__name__.startswith("transformers")
                    ):
                        return []
                    return original_extract_from_module(module, extract_func)
                except Exception:
                    # 不输出警告，静默失败
                    return []
            
            local_sources_watcher._extract_from_module = safe_extract_from_module
            patched = True
        
        return patched
            
    except Exception:
        # 静默失败，不输出警告
        return False


# Provide wrapper functions for common torch operations
def to_tensor(data, device: Optional[str] = None):
    """Convert data to a torch tensor on the specified device."""
    torch = get_torch()
    tensor = torch.tensor(data)
    if device is None:
        device = get_device()
    return tensor.to(device) 