from models.deepseek import request_deepseek
from models.qwen import request_qwen
from models.gemini import request_gemini
from tools.logger import get_logger

logger = get_logger(__name__)

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