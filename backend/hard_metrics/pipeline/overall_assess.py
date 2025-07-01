"""
论文整体评估模块
将整篇论文内容作为整体进行评估
"""
import os
import json
from typing import List, Dict, Any
from multiprocessing import Pool
import warnings

# 导入项目模块
from models.deepseek import request_deepseek
from models.qwen import request_qwen
from models.gemini import request_gemini
from tools.file_utils import read_pickle
from tools.logger import get_logger
from prompts.overall_assess_prompt import p_overall_content_logic

logger = get_logger(__name__)

def load_full_paper(pkl_path: str) -> str:
    """
    加载整篇论文内容
    
    Args:
        pkl_path: pickle文件路径
        
    Returns:
        str: 拼接后的完整论文内容
    """
    try:
        data = read_pickle(pkl_path)
        full_content = ""
        
        # 处理摘要
        if 'cn_abs' in data and isinstance(data['cn_abs'], str):
            full_content += f"摘要:\n{data['cn_abs']}\n\n"
            
        # 处理各章节
        chapters = data.get('chapters', [])
        for chapter in chapters:
            if isinstance(chapter, dict) and 'content' in chapter:
                full_content += f"{chapter.get('title', '未命名章节')}:\n{chapter['content']}\n\n"
                
        if not full_content:
            raise ValueError(f"没有找到有效的论文内容: {pkl_path}")
            
        logger.info(f'从 {pkl_path} 加载了完整论文内容，总长度: {len(full_content)}')
        return full_content
        
    except Exception as e:
        logger.error(f"加载论文内容失败: {e}")
        raise

def generate_overall_prompt(full_content: str) -> str:
    """
    生成整体评估提示词
    
    Args:
        full_content: 完整论文内容
        
    Returns:
        str: 格式化后的提示词
    """
    try:
        return p_overall_content_logic.format(
            paper_content=full_content
        )
    except KeyError as e:
        logger.error(f"提示词模板缺少必要参数: {e}")
        raise

def infer(pkl_path: str, out_dir: str, num_processes: int = 8, model_name: str = "deepseek-chat") -> None:
    """
    对论文进行推理
    
    Args:
        pkl_path: pickle文件路径
        out_dir: 输出目录
        num_processes: 进程数
        model_name: 使用的模型名称
        
    Raises:
        ChapterInferenceError: 当推理过程出错时抛出
    """
    try:
        os.makedirs(out_dir, exist_ok=True)
        
        # 1. 加载完整论文内容
        full_content = load_full_paper(pkl_path)
        
        # 2. 生成整体评估提示词
        prompt = generate_overall_prompt(full_content)
        logger.info(f'生成的整体评估提示词长度: {len(prompt)}')
        
        # 3. 调用模型进行评估
        if model_name.startswith("deepseek"):
            response = request_deepseek(prompt, model_name)
        elif model_name == "gemini":
            response = request_gemini(prompt)
        elif model_name == "qwen":
            response = request_qwen(prompt)
        else:
            raise ValueError(f"不支持的模型名称: {model_name}")
            
        # 4. 解析响应
        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            # 尝试提取JSON部分
            json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(1))
            else:
                result = {
                    "error": "无法解析模型响应",
                    "raw_response": response
                }
                
        # 5. 保存结果
        filename = os.path.basename(pkl_path)
        output_file = os.path.join(out_dir, filename.replace('.pkl', '_overall.json'))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=4)
            
        logger.info(f"整体评估完成，结果已保存到: {output_file}")
        return result
        
    except Exception as e:
        logger.error(f"整体评估过程出错: {e}")
        raise

if __name__ == "__main__":
    """
    测试函数，仅当本文件作为脚本执行时调用。
    """
    random.seed(42)
    
    try:
        # 从配置文件获取基础路径
        base_dir = FILE_CONFIG.get('base_dir')
        input_root = FILE_CONFIG.get('processed_data_dir')
        output_root = FILE_CONFIG.get('output_data_dir')
        
        input_dir = os.path.join(input_root, 'docx')
        output_dir = os.path.join(output_root, 'docx')

        # 获取所有pkl文件
        pkl_pattern = str(input_dir) + '/*.pkl'
        pkl_lst = glob(pkl_pattern)
        
        if not pkl_lst:
            logger.warning(f"在 {input_dir} 中没有找到要处理的PKL文件")
            
        # 处理每个文件
        for pkl_path in pkl_lst:
            try:
                logger.info(f"开始处理文件: {pkl_path}")
                infer(pkl_path, str(output_dir), num_processes=8)
            except Exception as e:
                logger.error(f"处理文件 {pkl_path} 时出错: {e}")
                continue
                
    except Exception as e:
        logger.error(f"程序执行出错: {e}")