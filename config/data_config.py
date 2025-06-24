"""
文件配置模块
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# 数据目录
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
OUTPUT_DATA_DIR = os.path.join(DATA_DIR, 'output')

FILE_CONFIG = {
    'encoding': 'utf-8',
    # 'base_dir': str(PROJECT_ROOT),  # 项目根目录
    # 'input_dir': 'input',  # 输入文件目录
    # 'output_dir': 'output',  # 输出文件目录
    'temp_dir': 'temp',  # 临时文件目录
    'log_dir': 'logs',  # 日志文件目录
    # 'allowed_extensions': {'.json', '.txt', '.md', '.pkl'},
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'base_dir': str(PROJECT_ROOT),  # 项目根目录
    'raw_data_dir': str(RAW_DATA_DIR),  # 原始数据目录
    'processed_data_dir': str(PROCESSED_DATA_DIR),  # 处理后数据目录
    'output_data_dir': str(OUTPUT_DATA_DIR),  # 输出数据目录
} 