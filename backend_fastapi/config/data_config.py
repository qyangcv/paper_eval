"""
数据和文件配置模块
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
BACKEND_FASTAPI_ROOT = Path(__file__).parent.parent.absolute()

# 数据目录
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
OUTPUT_DATA_DIR = os.path.join(DATA_DIR, 'output')

# 临时目录
TEMP_DIR = os.path.join(BACKEND_FASTAPI_ROOT, 'temp')
LOGS_DIR = os.path.join(BACKEND_FASTAPI_ROOT, 'logs')

# 文件配置
FILE_CONFIG = {
    'encoding': 'utf-8',
    'temp_dir': str(TEMP_DIR),
    'log_dir': str(LOGS_DIR),
    'max_file_size': 50 * 1024 * 1024,  # 50MB
    'allowed_extensions': {'.docx', '.doc', '.pdf', '.txt', '.md'},
    'upload_timeout': 300,  # 5分钟
    'processing_timeout': 1800,  # 30分钟
}

# 数据路径配置
DATA_PATHS = {
    'project_root': str(PROJECT_ROOT),
    'backend_root': str(BACKEND_FASTAPI_ROOT),
    'data_dir': str(DATA_DIR),
    'raw_data_dir': str(RAW_DATA_DIR),
    'processed_data_dir': str(PROCESSED_DATA_DIR),
    'output_data_dir': str(OUTPUT_DATA_DIR),
    'temp_dir': str(TEMP_DIR),
    'logs_dir': str(LOGS_DIR),
}

# 确保必要的目录存在
def ensure_directories():
    """确保所有必要的目录存在"""
    directories = [
        DATA_DIR,
        RAW_DATA_DIR, 
        PROCESSED_DATA_DIR,
        OUTPUT_DATA_DIR,
        TEMP_DIR,
        LOGS_DIR
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

# 在模块导入时创建目录
ensure_directories()
