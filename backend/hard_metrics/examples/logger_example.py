"""
日志使用示例
"""

from tools.logger import get_logger

# 获取日志记录器
logger = get_logger(__name__)

def main():
    # 不同级别的日志示例
    logger.debug("这是一条调试信息")  # 调试级别，默认不显示
    logger.info("这是一条普通信息")   # 信息级别
    logger.warning("这是一条警告信息") # 警告级别
    logger.error("这是一条错误信息")   # 错误级别
    logger.critical("这是一条严重错误信息") # 严重错误级别
    
    # 带变量的日志
    name = "测试"
    count = 5
    logger.info(f"处理{name}，共{count}条记录")
    
    # 异常日志
    try:
        1/0
    except Exception as e:
        logger.error(f"发生错误: {str(e)}", exc_info=True)  # exc_info=True 会记录完整的堆栈跟踪

if __name__ == "__main__":
    main() 