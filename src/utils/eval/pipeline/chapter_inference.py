"""
章节推理模块
用于对论文的各个章节进行质量评估
"""
# 确保能够导入项目模块
import os

# 导入项目模块
from config.data_config import FILE_CONFIG
from config.model_config import MODEL_CONFIG
from models import request_qwen, request_deepseek, request_gemini
from prompts import p_writing_quality
from utils.eval.tools.file_utils import read_pickle
from utils.eval.tools.logger import get_logger


# 导入第三方模块
import json
from typing import List, Dict, Any
# from transformers import AutoTokenizer
from multiprocessing import Pool
from glob import glob
import random
import warnings

# 使用torch_helper中的安全导入方法
try:
    from utils.eval.tools.torch_helper import get_transformers
    
    def _safe_import_transformers():
        return get_transformers()
except ImportError:
    # 如果torch_helper导入失败，继续使用原有的延迟导入方法
    _transformers = None
    _tokenizer = None

    def _safe_import_transformers():
        """Safely import transformers module without triggering Streamlit file watcher issues."""
        global _transformers
        if _transformers is None:
            try:
                import transformers
                _transformers = transformers
                return transformers
            except ImportError:
                warnings.warn("Failed to import transformers library. Tokenization functionality will be unavailable.")
                return None
        return _transformers

def _get_tokenizer(model_name):
    """Safely get a tokenizer with deferred import."""
    global _tokenizer
    if _tokenizer is None:
        transformers = _safe_import_transformers()
        if transformers:
            try:
                if 'qwen' in model_name.lower():
                    _tokenizer = transformers.AutoTokenizer.from_pretrained('Qwen/Qwen-7B-Chat')
                else:
                    _tokenizer = transformers.AutoTokenizer.from_pretrained('deepseek-ai/deepseek-llm-7b-chat')
                return _tokenizer
            except Exception as e:
                warnings.warn(f"Failed to initialize tokenizer: {e}")
                return None
    return _tokenizer

logger = get_logger(__name__)


def load_context(pkl_path: str, model_name: str) -> List[str]:
    """
    加载论文章节内容
    
    Args:
        pkl_path: pickle文件路径
        model_name: 模型名称
        
    Returns:
        List[str]: 章节内容列表
        
    Raises:
        ChapterInferenceError: 当加载过程出错时抛出
    """
        
    # if not model_name.startswith("deepseek"):
    #     tokenizer = AutoTokenizer.from_pretrained(MODEL_CONFIG['qwen']['model_name'])
        
    context_lst = []
    data = read_pickle(pkl_path)
        
    keys = list(data.keys())
    for i, k in enumerate(keys):
        if k == 'chapters':
            chapters_list = data.get(k, [])
            for chap_idx, chapter_data in enumerate(chapters_list):
                if isinstance(chapter_data, dict) and isinstance(chapter_data.get('content'), str):
                    c = chapter_data['content']
                    context_lst.append(c)
                else:
                    logger.warning(f"跳过章节 {chap_idx}，因为内容格式无效: {pkl_path}")
        elif isinstance(data[k], str):
            c = data[k]
            context_lst.append(c)
        else:
            logger.warning(f"跳过键 '{k}'，因为值不是字符串: {pkl_path}")

    if not context_lst:
        raise ValueError(f"没有找到有效的章节内容: {pkl_path}")

    logger.info(f'从 {pkl_path} 加载了 {len(context_lst)} 个章节用于论文写作质量评估')
    return context_lst

def load_prompts(context: List[str]) -> List[str]:
    """
    根据章节内容生成提示词列表
    
    Args:
        context: 章节内容列表
        
    Returns:
        List[str]: 提示词列表
    """
    prompt_lst = []
    for c in context:
        prompt = p_writing_quality.format(content=c)
        prompt_lst.append(prompt)
    logger.info(f'生成了 {len(prompt_lst)} 个提示词')
    return prompt_lst

def _request_model(args: tuple[str, str]):
    """根据模型名称调用对应的请求接口。

    Args:
        args: (prompt, model_name)

    Returns:
        str: 模型返回的结果 JSON 字符串
    """
    prompt, model_name = args
    try:
        if model_name.startswith("deepseek"):
            response = request_deepseek(prompt, model_name)
        elif model_name == "gemini":
            response = request_gemini(prompt)
        elif model_name == "qwen":
            response = request_qwen(prompt)
        else:
            raise ValueError(f"Invalid model name: {model_name}")
        return {'input': prompt, 'output': response}
        # return response
    except Exception as e:
        logger.error(f"不存在该模型: {e}")
        return {'input': prompt, 'error': str(e)}

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
        # 确保输出目录存在
        os.makedirs(out_dir, exist_ok=True)
        
        # 加载上下文和提示词
        logger.info(f"使用模型: {model_name}")
        
        context = load_context(pkl_path, model_name)
        prompts = load_prompts(context)
        
        # 准备进程池参数
        pool_args = [(prompt, model_name) for prompt in prompts]
        
        # 使用进程池处理章节
        with Pool(processes=num_processes) as pool:
            results = pool.map(_request_model, pool_args)
        
        # 保存结果
        filename = os.path.basename(pkl_path)
        output_file = os.path.join(out_dir, filename.replace('.pkl', '.json'))
        
        with open(output_file, 'w', encoding=FILE_CONFIG['encoding']) as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
            
        logger.info(f"推理完成，结果已保存到: {output_file}")
        
    except Exception as e:
        logger.error(f"推理过程出错: {e}")

def chapter_inference():
    """
    章节推理主函数
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

if __name__ == "__main__":
    chapter_inference()