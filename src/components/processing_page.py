import streamlit as st
import time
from services.document_processor import convert_word_to_html, convert_word_to_html_with_math, simulate_analysis_with_toc, extract_toc_from_docx

def render_processing_page():
    """渲染处理页面"""
    # 检查是否有上传的文件
    if not hasattr(st.session_state, 'uploaded_file') or st.session_state.uploaded_file is None:
        st.warning("请先上传文件")
        st.session_state.current_page = 'upload'
        st.rerun()
    
    # 显示处理进度
    st.markdown('<h1 class="main-header">⚙️ 文档处理中...</h1>', unsafe_allow_html=True)
    
    # 显示上传的文件信息
    st.markdown(f"""
    <div style="background: linear-gradient(to right, rgba(67, 97, 238, 0.05), rgba(76, 201, 240, 0.03)); 
                border-radius: 12px; padding: 1rem 1.5rem; margin-bottom: 2rem; 
                display: flex; align-items: center;">
        <div style="background-color: var(--primary-color); border-radius: 50%; width: 40px; height: 40px;
                    display: flex; align-items: center; justify-content: center; margin-right: 1rem;">
            <span style="color: white; font-size: 1.5rem;">📄</span>
        </div>
        <div>
            <div style="font-size: 1.1rem; font-weight: 600; color: var(--text-primary);">
                {st.session_state.uploaded_file.name}
            </div>
            <div style="color: var(--text-secondary); font-size: 0.85rem;">
                正在处理文档并进行智能分析，请稍候...
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 创建进度条
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 处理步骤
    steps = [
        "正在加载文档...",
        "提取文档结构...",
        "处理章节内容...",
        "生成HTML预览...",
        "进行论文质量评估...",
        "生成评分与建议..."
    ]
    
    # 进行文档处理流程
    try:
        # 步骤1: 加载文档
        status_text.text(steps[0])
        progress_bar.progress(1/len(steps))
        time.sleep(0.5)
        
        # 步骤2: 提取文档结构
        status_text.text(steps[1])
        progress_bar.progress(2/len(steps))
        # 提取目录结构
        st.session_state.toc_items = extract_toc_from_docx(st.session_state.uploaded_file)
        time.sleep(0.5)
        
        # 步骤3: 处理章节内容
        status_text.text(steps[2])
        progress_bar.progress(3/len(steps))
        time.sleep(0.7)
        
        # 步骤4: 生成HTML预览
        status_text.text(steps[3])
        progress_bar.progress(4/len(steps))
        # 使用增强版转换函数，支持数学公式和复杂格式
        html_content = convert_word_to_html_with_math(st.session_state.uploaded_file)
        st.session_state.word_html = html_content
        time.sleep(0.5)
        
        # 步骤5: 进行论文质量评估
        status_text.text(steps[4])
        progress_bar.progress(5/len(steps))
        
        # 步骤6: 生成评分与建议
        status_text.text(steps[5])
        progress_bar.progress(1.0)
        
        # 调用论文评估函数生成分析结果
        analysis_result = simulate_analysis_with_toc(st.session_state.uploaded_file)
        st.session_state.analysis_result = analysis_result
        
        # 更新toc_items，确保包含分析结果
        if analysis_result and 'chapters' in analysis_result:
            st.session_state.toc_items = analysis_result['chapters']
        
        # 添加1秒延迟，让用户感知处理完成
        time.sleep(1)
        
        # 显示成功消息
        st.success("文档处理和分析已完成！")
        time.sleep(0.7)
        
        # 处理完成，跳转到结果页面
        st.session_state.current_page = 'results'
        st.rerun()
    
    except Exception as e:
        # 处理错误情况
        st.error(f"处理文档时发生错误: {str(e)}")
        st.button("重新上传", on_click=lambda: setattr(st.session_state, 'current_page', 'upload')) 