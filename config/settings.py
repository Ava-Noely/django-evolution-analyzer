"""
项目配置 - 单文件配置
"""
from pathlib import Path
import os


class Config:
    """项目配置类"""

    # 基础路径
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    RAW_DATA_DIR = DATA_DIR / "raw"
    PROCESSED_DATA_DIR = DATA_DIR / "processed"

    # Django仓库配置
    DJANGO_REPO_URL = "https://github.com/django/django.git"
    DJANGO_REPO_PATH = RAW_DATA_DIR / "django"

    # 分析配置
    SAMPLE_SIZE = 100
    MAX_COMMITS = 1000

    @classmethod
    def setup_directories(cls):
        """创建必要的目录结构"""
        directories = [
            cls.RAW_DATA_DIR,
            cls.PROCESSED_DATA_DIR,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"[配置] 目录确认: {directory}")


# 全局配置实例
config = Config()
config.setup_directories()