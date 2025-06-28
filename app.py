import streamlit as st
import sys
import os
import warnings
import atexit
import gc

# 前端组件导入
from frontend.utils.session_state import init_session_state, reset_session_state
from frontend.styles.custom_styles import apply_custom_styles
from frontend.components.upload_page import render_upload_page
from frontend.components.processing_page import render_processing_page
from frontend.components.results_page import render_results_page

# 后端工具导入
try:
    from backend.hard_metrics.tools.torch_helper import patch_streamlit_watcher
except ImportError:
    patch_streamlit_watcher = None

# 创建自定义警告过滤器
class TorchWatcherFilter(warnings.WarningMessage):
    def __init__(self):
        pass
    
    def __eq__(self, other):
        return (isinstance(other, warnings.WarningMessage) and 
                "file watcher" in str(other.message))

# 完全抑制来自torch_helper的警告
warnings.filterwarnings("ignore", category=UserWarning)

# 应用警告过滤器
warnings.resetwarnings()
warnings.filterwarnings("ignore", message=".*file watcher.*")
warnings.filterwarnings("ignore", message=".*torch.*")
# 忽略ResourceWarning警告
warnings.filterwarnings("ignore", category=ResourceWarning)

# 程序退出时的清理函数
def cleanup():
    """程序退出时执行的清理工作"""
    # 强制回收垃圾对象
    gc.collect()
    
    # 关闭所有可能打开的文件
    for fd in range(3, 1000):  # 跳过标准输入输出错误
        try:
            os.close(fd)
        except:
            pass

# 注册退出时的清理函数
atexit.register(cleanup)

# 创建必要的数据目录
def create_data_directories():
    """创建必要的数据目录结构"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    directories = [
        os.path.join(project_root, "data", "raw", "docx"),
        os.path.join(project_root, "data", "raw", "docx", "images"),
        os.path.join(project_root, "data", "processed", "docx"),
        os.path.join(project_root, "data", "output")
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# 页面配置必须是第一个 Streamlit 命令
st.set_page_config(
    page_title="Word文档分析器",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    """主应用入口函数"""
    # 创建必要的数据目录
    create_data_directories()
    
    # 初始化会话状态
    init_session_state()
    
    # 应用自定义样式
    apply_custom_styles()
    
    # 创建页面容器
    page_container = st.container()
    
    # 清除之前的内容
    page_container.empty()
    
    # 页面路由
    with page_container:
        if st.session_state.current_page == 'upload':
            render_upload_page()
        elif st.session_state.current_page == 'processing':
            # 在这里应用补丁，仅在需要时
            if 'torch_patch_applied' not in st.session_state:
                try:
                    # 添加路径并应用补丁
                    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                    
                    # 静默应用补丁
                    if patch_streamlit_watcher:
                        try:
                            patch_streamlit_watcher()
                            st.session_state.torch_patch_applied = True
                        except:
                            pass
                except:
                    pass
            
            render_processing_page()
        elif st.session_state.current_page == 'results':
            render_results_page()

if __name__ == "__main__":
    main() 