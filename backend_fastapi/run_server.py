"""
服务器启动脚本
提供便捷的服务器启动和配置功能
"""

import os
import sys
import argparse
import uvicorn
import logging.config
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from backend_fastapi.config.app_config import get_app_config, get_env_status
from backend_fastapi.config.log_config import get_log_config
from backend_fastapi.tools.logger import get_logger

def setup_logging(environment: str = 'development'):
    """
    设置日志配置
    
    Args:
        environment: 环境类型
    """
    log_config = get_log_config(environment)
    logging.config.dictConfig(log_config)

def check_dependencies():
    """检查必要的依赖"""
    logger = get_logger(__name__)

    required_packages = [
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('python-multipart', 'multipart'),
        ('aiofiles', 'aiofiles'),
        ('python-docx', 'docx'),
        ('psutil', 'psutil')
    ]

    missing_packages = []
    for package_name, import_name in required_packages:
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)

    if missing_packages:
        logger.error(f"缺少必要的依赖包: {', '.join(missing_packages)}")
        logger.error("请运行以下命令安装:")
        logger.error(f"pip install {' '.join(missing_packages)}")
        return False

    logger.info("所有必要依赖已安装")
    return True

def check_environment():
    """检查环境配置"""
    logger = get_logger(__name__)
    issues = []

    # 检查API密钥
    api_keys = {
        'DEEPSEEK_API_KEY': 'DeepSeek API密钥',
        'GEMINI_API_KEY': 'Gemini API密钥',
        'QWEN_API_KEY': 'Qwen API密钥'
    }

    available_keys = []
    for key, description in api_keys.items():
        if os.getenv(key):
            available_keys.append(description)
        else:
            issues.append(f"未设置 {key} ({description})")

    if available_keys:
        logger.info(f"已配置的API密钥: {', '.join(available_keys)}")
    else:
        logger.warning("未配置任何API密钥，某些功能可能无法使用")

    # 检查目录权限
    from backend_fastapi.config.data_config import DATA_PATHS

    for path_name, path_value in DATA_PATHS.items():
        try:
            os.makedirs(path_value, exist_ok=True)
            # 测试写入权限
            test_file = os.path.join(path_value, '.test_write')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except Exception as e:
            issues.append(f"目录 {path_name} ({path_value}) 权限问题: {e}")

    if not issues:
        logger.info("环境配置检查通过")
        return True
    else:
        logger.warning("环境配置问题:")
        for issue in issues:
            logger.warning(f"  - {issue}")
        return False

def run_server(
    host: str = None,
    port: int = None,
    reload: bool = None,
    workers: int = None,
    environment: str = 'development',
    check_env: bool = True
):
    """
    运行服务器
    
    Args:
        host: 服务器主机地址
        port: 服务器端口
        reload: 是否启用自动重载
        workers: 工作进程数
        environment: 环境类型
        check_env: 是否检查环境
    """
    # 设置日志
    setup_logging(environment)
    logger = get_logger(__name__)

    # 报告环境配置状态
    env_status = get_env_status()
    if env_status['loaded']:
        logger.info(f"已加载环境配置文件: {env_status['path']}")
    elif env_status['error']:
        logger.warning(env_status['error'])

    logger.info("启动论文评价分析系统后端服务器")
    logger.info("=" * 50)
    
    # 检查依赖和环境
    if check_env:
        logger.info("检查系统依赖...")
        if not check_dependencies():
            sys.exit(1)

        logger.info("检查环境配置...")
        check_environment()  # 不强制退出，只是警告
    
    # 获取配置
    config = get_app_config()
    server_config = config['server']
    
    # 使用传入的参数或配置文件的值
    final_host = host or server_config['host']
    final_port = port or server_config['port']
    final_reload = reload if reload is not None else server_config['reload']
    final_workers = workers or server_config['workers']
    
    logger.info(f"服务器配置:")
    logger.info(f"  - 地址: {final_host}:{final_port}")
    logger.info(f"  - 环境: {environment}")
    logger.info(f"  - 自动重载: {final_reload}")
    logger.info(f"  - 工作进程: {final_workers}")
    
    # 启动服务器
    try:
        logger.info("启动服务器...")

        # 创建自定义的uvicorn日志配置
        uvicorn_log_config = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "access": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
                "access": {
                    "formatter": "access",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
                "uvicorn.error": {"handlers": ["default"], "level": "INFO", "propagate": False},
                "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
            },
        }

        uvicorn.run(
            "backend_fastapi.main:app",
            host=final_host,
            port=final_port,
            reload=final_reload,
            workers=final_workers if not final_reload else 1,  # reload模式下只能使用1个worker
            log_config=uvicorn_log_config,  # 使用统一的日志配置
            access_log=True
        )
        
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='论文评价分析系统后端服务器')
    
    parser.add_argument('--host', default=None, help='服务器主机地址')
    parser.add_argument('--port', type=int, default=None, help='服务器端口')
    parser.add_argument('--reload', action='store_true', help='启用自动重载（开发模式）')
    parser.add_argument('--no-reload', action='store_true', help='禁用自动重载')
    parser.add_argument('--workers', type=int, default=None, help='工作进程数')
    parser.add_argument('--env', choices=['development', 'production', 'testing'], 
                       default='development', help='环境类型')
    parser.add_argument('--no-check', action='store_true', help='跳过环境检查')
    
    args = parser.parse_args()
    
    # 处理reload参数
    reload = None
    if args.reload:
        reload = True
    elif args.no_reload:
        reload = False
    
    # 运行服务器
    run_server(
        host=args.host,
        port=args.port,
        reload=reload,
        workers=args.workers,
        environment=args.env,
        check_env=not args.no_check
    )

if __name__ == "__main__":
    main()
