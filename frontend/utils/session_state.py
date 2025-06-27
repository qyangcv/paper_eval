import streamlit as st
import time

def init_session_state():
    """初始化会话状态"""
    # 如果是第一次加载，设置默认状态
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'upload'
    
    # 如果上传文件状态不存在，初始化为None
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    
    # 如果文档HTML不存在，初始化为None
    if 'word_html' not in st.session_state:
        st.session_state.word_html = None
    
    # 如果目录项不存在，初始化为空列表
    if 'toc_items' not in st.session_state:
        st.session_state.toc_items = []
    
    # 如果分析结果不存在，初始化为空列表
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = []
    
    # 如果结构化内容不存在，初始化为None
    if 'structured_content' not in st.session_state:
        st.session_state.structured_content = None
    
    # 如果消息轮播器不存在，初始化为None
    if 'message_rotator' not in st.session_state:
        st.session_state.message_rotator = None

def reset_session_state():
    """重置会话状态"""
    st.session_state.current_page = 'upload'
    st.session_state.uploaded_file = None
    st.session_state.word_html = None
    st.session_state.toc_items = []
    st.session_state.analysis_results = []
    st.session_state.structured_content = None
    
    # 重置轮播相关状态
    if 'carousel_index' in st.session_state:
        st.session_state.carousel_index = 0
    if 'last_update_time' in st.session_state:
        st.session_state.last_update_time = time.time()
    if 'processing_active' in st.session_state:
        st.session_state.processing_active = False
    if 'processing_complete' in st.session_state:
        st.session_state.processing_complete = False 