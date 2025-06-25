"""
Paper evaluation package for document processing and quality assessment.
"""

# Import main modules
from . import infer
from . import test_paper_eval
from . import full_paper_eval

# Import sub-packages
from . import config
from . import models
from . import pipeline
from . import prompts
from . import tools

# Expose key functions
from .infer import run_inference, main as run_main
from .test_paper_eval import prepare_sample_file, run_inference as run_paper_inference, convert_output, main as eval_main
from .full_paper_eval import process_docx_file, load_chapters, evaluate_overall, score_paper, main as full_eval_main

__all__ = [
    # Modules
    'infer',
    'test_paper_eval',
    'full_paper_eval',
    'config',
    'models',
    'pipeline',
    'prompts',
    'tools',
    
    # Functions
    'run_inference',
    'run_main',
    'prepare_sample_file',
    'run_paper_inference',
    'convert_output',
    'eval_main',
    'process_docx_file',
    'load_chapters',
    'evaluate_overall',
    'score_paper',
    'full_eval_main'
]
