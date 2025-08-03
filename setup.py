#!/usr/bin/env python3
"""
OpenLLM Toolkit - Setup Script
Package installation and distribution configuration
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="openllm-toolkit",
    version="1.0.0",
    author="Kiwon Bowens",
    author_email="Heloimai@helo-im.ai",
    description="Universal Free LLM Integration Platform",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Sourcesiri-Kamelot/swiftagent",
    project_urls={
        "Bug Reports": "https://github.com/Sourcesiri-Kamelot/swiftagent/issues",
        "Source": "https://github.com/Sourcesiri-Kamelot/swiftagent",
        "Documentation": "https://github.com/Sourcesiri-Kamelot/swiftagent#readme",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.20.0",
        ],
        "full": [
            "torch>=1.12.0",
            "transformers>=4.20.0",
            "accelerate>=0.20.0",
            "opencv-python>=4.6.0",
            "pytesseract>=0.3.10",
        ],
    },
    entry_points={
        "console_scripts": [
            "openllm=Interface.cli:main",
            "openllm-mcp=MCP.mcp_server:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.yml", "*.md", "*.txt"],
    },
    zip_safe=False,
    keywords="ai llm machine-learning openai ollama huggingface azure amazon",
) 