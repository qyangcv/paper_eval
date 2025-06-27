import streamlit as st
import time
import json
import random
import uuid
import base64
from ..services.document_processor import convert_word_to_html_with_math, simulate_analysis_with_toc, extract_toc_from_docx

# 使用iframe和HTML/CSS/JS实现客户端轮播效果
def display_carousel_messages():
    """使用iframe和HTML实现轮播消息，确保JavaScript正常运行"""
    # 耐心等待的轮播消息
    waiting_messages = [
        "🧾 别担心，系统不会笑你写得不对——它最多安静地给你打个建议分而已……",
        "🧠 正在调用秃头换来的智慧引擎, 为你论文做深度解析, 请稍候!",
        "✨ AI助教正在努力理解你的精妙论点, 并试图不露出看不懂但很震惊的表情~",
        "🔍 你的论文现在正被放在显微镜下, 一字一句都逃不过系统的学术法眼！",
        "🧃 论文太卷, 系统先喝口奶茶缓一缓……哦不, 继续处理中!",
        "🛠️ 正在为你的论文匹配金句评级, 看看你有没有写出能让导师点头的那一句!",
        "⏳ 系统已进入批改状态，现在它比你还想知道这篇论文能得几分……",
        "🪄 论文即将被施以AI魔法, 耐心等待, 评分结果马上出炉!",
        "📈 别盯着进度条啦~ 你都写完了这么难的论文, 再等等这点时间也不算啥!",
        "📚 正在分析正文逻辑中……别担心, 论文再绕, AI也能找到主线剧情!"
    ]

    # 创建唯一ID用于轮播容器
    carousel_id = f"carousel-{str(uuid.uuid4())[:8]}"
    
    # 构建完整的HTML页面，包含所有CSS和JavaScript
    carousel_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                margin: 0;
                padding: 0;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }}
            .carousel-container {{
                color: #333;
                padding: 1.2rem;
                border-radius: 12px;
                background-color: rgba(240, 242, 246, 0.4);
                box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                margin: 0;
                height: 80px;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
            }}
            .carousel-message {{
                font-size: 1.1rem;
                font-weight: 500;
                text-align: center;
                opacity: 1;
                transition: opacity 0.5s ease;
            }}
        </style>
    </head>
    <body>
        <div class="carousel-container" id="{carousel_id}-container">
            <div class="carousel-message" id="{carousel_id}-message">
                {waiting_messages[0]}
            </div>
        </div>
        
        <script>
            // 定义消息数组
            const messages = {json.dumps(waiting_messages)};
            let currentIndex = 0;
            
            // 更新消息的函数
            function updateMessage() {{
                const messageElement = document.getElementById('{carousel_id}-message');
                
                // 淡出效果
                messageElement.style.opacity = 0;
                
                // 等待淡出完成后更新文本并淡入
                setTimeout(() => {{
                    currentIndex = (currentIndex + 1) % messages.length;
                    messageElement.innerText = messages[currentIndex];
                    messageElement.style.opacity = 1;
                }}, 500);
            }}
            
            // 每3秒更新一次消息
            setInterval(updateMessage, 3000);
        </script>
    </body>
    </html>
    """
    
    # 将HTML编码为base64
    b64_html = base64.b64encode(carousel_html.encode()).decode()
    
    # 使用iframe嵌入轮播器，确保JavaScript在隔离环境中正确运行
    st.markdown(f"""
        <iframe src="data:text/html;base64,{b64_html}" 
                height="100" 
                width="100%" 
                frameBorder="0" 
                scrolling="no"
                style="margin: 2rem 0;">
        </iframe>
    """, unsafe_allow_html=True)

def render_processing_page():
    """渲染处理页面"""
    # 检查是否有上传的文件
    if not hasattr(st.session_state, 'uploaded_file') or st.session_state.uploaded_file is None:
        st.warning("请先上传文件")
        st.session_state.current_page = 'upload'
        st.rerun()
    
    # 添加CSS来隐藏上一页的按钮
    st.markdown("""
    <style>
        /* 隐藏上传页面的"开始分析"按钮 */
        button[kind="primary"] {
            display: none !important;
        }
        
        /* 隐藏上传页面的文件上传器 */
        [data-testid="stFileUploader"] {
            display: none !important;
        }
        
        /* 隐藏上传成功的提示 */
        .element-container:has(div[style*="background: var(--success-light)"]) {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
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
    
    # 创建进度条和状态信息显示
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    # 显示轮播消息（使用iframe解决方案）
    display_carousel_messages()
    
    # 初始化处理状态变量
    if 'processing_complete' not in st.session_state:
        st.session_state.processing_complete = False
    
    if 'processing_active' not in st.session_state:
        st.session_state.processing_active = False
        
    # 直接处理文档 - 移除嵌套的条件判断，确保每次页面加载都会处理文档一次
    # 这样可以避免因条件判断错误导致流程被跳过
    if not st.session_state.processing_complete:
        try:
            st.session_state.processing_active = True
            
            # 定义进度回调函数，用于更新进度条和状态信息
            def update_progress(progress_value, status_text):
                progress_bar.progress(progress_value)
                status_container.info(f"**当前步骤:** {status_text}")
            
            # 前置处理阶段 (占总进度的5%)
            update_progress(0.01, "正在初始化处理环境...")
            time.sleep(0.3)
            
            # 提取目录结构
            update_progress(0.02, "正在提取文档结构...")
            st.session_state.toc_items = extract_toc_from_docx(st.session_state.uploaded_file)
            time.sleep(0.5)
            
            # 生成HTML预览
            update_progress(0.03, "正在生成文档预览...")
            html_content = convert_word_to_html_with_math(st.session_state.uploaded_file)
            st.session_state.word_html = html_content
            time.sleep(0.5)
            
            update_progress(0.05, "文档预处理完成，准备开始评估...")
            
            # 调用论文评估函数，传递进度回调函数，比例为5%-95%
            analysis_result = simulate_analysis_with_toc(
                st.session_state.uploaded_file,
                progress_callback=lambda prog, text: update_progress(0.05 + prog * 0.90, text)
            )
            
            # 最终处理阶段 (占总进度的5%)
            update_progress(0.96, "正在整理评估结果...")
            time.sleep(0.3)
            
            # 更新toc_items，确保包含分析结果
            if analysis_result and 'chapters' in analysis_result:
                st.session_state.toc_items = analysis_result['chapters']
            
            # 保存分析结果到会话状态
            st.session_state.analysis_result = analysis_result
            
            update_progress(0.98, "正在准备结果页面...")
            time.sleep(0.3)
            
            # 完成处理
            update_progress(1.0, "处理完成！")
            
            # 设置处理完成标志
            st.session_state.processing_complete = True
            st.session_state.processing_active = False
            
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
            
            # 重置处理状态以便下次使用
            st.session_state.processing_active = False
            st.session_state.processing_complete = False
    else:
        # 如果已经完成，直接跳转到结果页面
        st.session_state.current_page = 'results'
        st.rerun() 