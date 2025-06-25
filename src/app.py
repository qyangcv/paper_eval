import streamlit as st
import sys
import os
import warnings

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

# 页面配置必须是第一个 Streamlit 命令
st.set_page_config(
    page_title="Word文档分析器",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    """主应用入口函数"""
    # 在需要时才进行导入，减少初始加载时间
    from utils.session_state import init_session_state, reset_session_state
    
    # 初始化会话状态
    init_session_state()
    
    # 应用自定义样式
    from styles.custom_styles import apply_custom_styles
    apply_custom_styles()
    
    # 创建页面容器
    page_container = st.container()
    
    # 清除之前的内容
    page_container.empty()
    
    # 页面路由 - 按需导入对应组件
    with page_container:
        if st.session_state.current_page == 'upload':
            from components.upload_page import render_upload_page
            render_upload_page()
        elif st.session_state.current_page == 'processing':
            # 在文件上传后才需要导入处理组件
            from components.processing_page import render_processing_page
            
            # 在这里应用补丁，仅在需要时
            if 'torch_patch_applied' not in st.session_state:
                try:
                    # 尝试从torch_helper导入补丁函数
                    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                    from utils.eval.tools.torch_helper import patch_streamlit_watcher
                    
                    # 静默应用补丁
                    try:
                        patch_streamlit_watcher()
                        st.session_state.torch_patch_applied = True
                    except:
                        pass
                except:
                    pass
            
            render_processing_page()
        elif st.session_state.current_page == 'results':
            from components.results_page import render_results_page
            render_results_page()

if __name__ == "__main__":
    main() 