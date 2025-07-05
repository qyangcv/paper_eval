import streamlit as st
import os

def render_feature_card(emoji, title, description, color):
    return f"""
    <div style="flex: 1; min-width: 300px; background: white; padding: 2rem; border-radius: 12px; 
                box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: left; margin: 1rem;">
        <div style="font-size: 2.5rem; color: var({color}); margin-bottom: 1rem;">{emoji}</div>
        <h4 style="font-weight: 600; margin-bottom: 1rem; font-size: 1.2rem;">{title}</h4>
        <p style="color: var(--text-secondary); font-size: 1rem; line-height: 1.6;">{description}</p>
    </div>
    """

def render_model_config_modal():
    """
    渲染API配置弹窗
    """
    # 使用会话状态来存储API Keys
    if 'api_keys' not in st.session_state:
        st.session_state.api_keys = {
            'deepseek': '',
            'gemini': '',
            'gpt': '',
        }
    
    with st.expander("🔧 配置模型API密钥"):
        st.markdown("### API密钥配置")
        st.markdown("请输入您的API密钥，以便使用相应的模型服务。密钥将存储在当前会话中。")
        
        # DeepSeek API密钥
        st.session_state.api_keys['deepseek'] = st.text_input(
            "DeepSeek API密钥",
            value=st.session_state.api_keys.get('deepseek', ''),
            type="password",
            help="输入DeepSeek API密钥，用于DeepSeek模型分析"
        )
        
        # Gemini API密钥
        st.session_state.api_keys['gemini'] = st.text_input(
            "Gemini API密钥",
            value=st.session_state.api_keys.get('gemini', ''),
            type="password",
            help="输入Gemini API密钥，用于Gemini模型分析"
        )
        
        # GPT API密钥
        st.session_state.api_keys['gpt'] = st.text_input(
            "GPT API密钥",
            value=st.session_state.api_keys.get('gpt', ''),
            type="password",
            help="输入OpenAI API密钥，用于GPT模型分析"
        )
        
        # 保存按钮
        if st.button("保存配置"):
            st.success("API密钥配置已保存！")

# ------------------- 弹出式 API 配置对话框 -------------------
@st.dialog("🔧 配置模型API密钥", width="large")
def api_config_dialog():
    """模型 API Key 配置对话框 (Session State 内存储)"""
    if 'api_keys' not in st.session_state:
        st.session_state.api_keys = {
            'deepseek': '',
            'gemini': '',
            'gpt': '',
        }

    st.markdown("### API密钥配置")
    st.markdown("请输入各模型的 API Key，信息仅保存在本次会话中。")

    st.session_state.api_keys['deepseek'] = st.text_input(
        "DeepSeek API密钥",
        value=st.session_state.api_keys.get('deepseek', ''),
        type="password",
    )
    st.session_state.api_keys['gemini'] = st.text_input(
        "Gemini API密钥",
        value=st.session_state.api_keys.get('gemini', ''),
        type="password",
    )
    st.session_state.api_keys['gpt'] = st.text_input(
        "GPT API密钥",
        value=st.session_state.api_keys.get('gpt', ''),
        type="password",
    )

    if st.button("保存配置"):
        st.success("API密钥配置已保存！")
        # 关闭对话框
        st.session_state['api_cfg_open'] = False
        st.rerun()

def render_upload_page():
    """渲染上传页面"""
    st.markdown('<h1 class="main-header">📄 Word文档分析器</h1>', unsafe_allow_html=True)
    
    # 上传区域
    st.markdown("""
    <div style="background: white; padding: 2rem; border-radius: 16px; box-shadow: 0 8px 30px rgba(0,0,0,0.08); margin-bottom: 3rem;">
        <div style="display: flex; align-items: flex-start; gap: 2rem;">
            <div style="flex: 0 0 auto; text-align: center;">
                <div style="width: 100px; height: 100px; margin: 0 auto; background: linear-gradient(45deg, var(--primary-color), var(--primary-light)); 
                            border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                    <span style="font-size: 3rem;">📤</span>
                </div>
            </div>
            <div style="flex: 1;">
                <h3 style="font-weight: 700; margin-bottom: 1rem; color: var(--primary-color);">
                    上传文档
                </h3>
                <p style="color: var(--text-secondary); margin-bottom: 1rem; font-size: 0.95rem; line-height: 1.6;">
                    支持.docx格式文档，自动识别图片、表格和复杂排版
                </p>
                <div class="supported-features" style="display: flex; gap: 1.5rem; margin-bottom: 1rem;">
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="color: var(--success-color);">✓</span>
                        <span style="color: var(--text-secondary); font-size: 0.9rem;">图片和表格</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="color: var(--success-color);">✓</span>
                        <span style="color: var(--text-secondary); font-size: 0.9rem;">数学公式</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="color: var(--success-color);">✓</span>
                        <span style="color: var(--text-secondary); font-size: 0.9rem;">章节结构</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                        <span style="color: var(--success-color);">✓</span>
                        <span style="color: var(--text-secondary); font-size: 0.9rem;">智能优化</span>
                    </div>
                </div>
            </div>
            <div style="flex: 0 0 200px; display: flex; flex-direction: column; gap: 1rem;">
    """, unsafe_allow_html=True)
    
    # 文件上传组件和按钮放在右侧
    uploaded_file = st.file_uploader(
        "选择Word文档",
        type=['docx'],
        help="支持包含图片和复杂格式的Word文档",
        label_visibility="collapsed"
    )
    
    # 添加模型选择下拉框
    # 初始化模型选择状态
    if 'selected_model' not in st.session_state:
        st.session_state.selected_model = 'deepseek'
    
    # 初始化 API Key 存储
    if 'api_keys' not in st.session_state:
        st.session_state.api_keys = {
            'deepseek': '',
            'gemini': '',
            'gpt': '',
        }
    
    # 模型选择下拉框
    st.session_state.selected_model = st.selectbox(
        "选择分析模型",
        options=['deepseek', 'gemini', 'gpt', 'none'],
        format_func=lambda x: {
            'deepseek': 'DeepSeek',
            'gemini': 'Gemini',
            'gpt': 'GPT',
            'none': '无模型分析'
        }.get(x, x),
        index=['deepseek', 'gemini', 'gpt', 'none'].index(st.session_state.selected_model)
    )

    # 当前模型展示 + 齿轮按钮
    info_col, gear_col = st.columns([5, 1])
    with info_col:
        st.markdown(f"**当前模型:** {st.session_state.selected_model}")
    with gear_col:
        if st.button("⚙️", key="open_api_cfg", help="配置API密钥", use_container_width=True):
            st.session_state['api_cfg_open'] = True

    # 如果会话状态标记为打开，则渲染对话框
    if st.session_state.get('api_cfg_open', False):
        api_config_dialog()
    
    if uploaded_file is not None:
        st.markdown("""
        <div style="background: var(--success-light); border-radius: 12px; padding: 0.75rem; margin-bottom: 0.5rem;">
            <div style="display: flex; align-items: center; gap: 0.5rem;">
                <div style="width: 20px; height: 20px; background: var(--success-color); border-radius: 50%; 
                            display: flex; align-items: center; justify-content: center; color: white; font-size: 0.8rem;">✓</div>
                <div style="font-size: 0.9rem; color: var(--success-color);">文件已上传</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.session_state.uploaded_file = uploaded_file
        
        if st.button("🚀 开始分析", type="primary", use_container_width=True):
            selected_model = st.session_state.selected_model

            # 若未配置任何 API Key 且未选择 none，则给出提示
            if selected_model != 'none' and not st.session_state.api_keys.get(selected_model):
                st.error("请先在右侧⚙️中配置对应模型的API密钥！")
                st.stop()

            # 保存选择的模型到会话状态
            st.session_state.model_for_analysis = selected_model

            # 根据配置写入环境变量
            if selected_model == 'deepseek' and st.session_state.api_keys.get('deepseek'):
                os.environ["DEEPSEEK_API_KEY"] = st.session_state.api_keys['deepseek']
            elif selected_model == 'gemini' and st.session_state.api_keys.get('gemini'):
                os.environ["GEMINI_API_KEY"] = st.session_state.api_keys['gemini']
            elif selected_model == 'gpt' and st.session_state.api_keys.get('gpt'):
                os.environ["OPENAI_API_KEY"] = st.session_state.api_keys['gpt']
            
            st.session_state.current_page = 'processing'
            st.rerun()
    
    st.markdown("</div></div></div>", unsafe_allow_html=True)