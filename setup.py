#!/usr/bin/env python3
"""
OpenClaw 轻量化三层记忆模型 - 安装脚本
Setup script for OpenClaw Lite Memory System

@author: DataBot
@version: 1.0.0
"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取README文件
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding="utf-8")

# 读取版本号
version = "1.0.0"

setup(
    name="openclaw-memory-lite",
    version=version,
    author="DataBot",
    author_email="databot@openclaw.ai",
    description="轻量化三层记忆模型 - 智能捕获、向量搜索、长期存档",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/openclaw/memory-lite",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21.0",
        "pyyaml>=6.0",
        "loguru>=0.6.0",
        "typer>=0.7.0",
    ],
    extras_require={
        "advanced": [
            "lancedb>=0.3.0",
            "sentence-transformers>=2.2.0",
        ],
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "memory-lite=memory_lite.main:main",
            "memory=memory_lite.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)