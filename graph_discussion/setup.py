"""Setup script for the Multi-Agent Discussion Framework."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="graph_discussion",
    version="1.0.0",
    author="AI Architect Team",
    author_email="team@ai-architect.com",
    description="A sophisticated multi-agent discussion framework built with LangGraph",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/multi-agent-discussion-framework",
    packages=find_packages(),
    # classifiers=[
    #     "Development Status :: 4 - Beta",
    #     "Intended Audience :: Developers",
    #     "Intended Audience :: Science/Research",
    #     "License :: OSI Approved :: MIT License",
    #     "Operating System :: OS Independent",
    #     "Programming Language :: Python :: 3",
    #     "Programming Language :: Python :: 3.8",
    #     "Programming Language :: Python :: 3.9",
    #     "Programming Language :: Python :: 3.10",
    #     "Programming Language :: Python :: 3.11",
    #     "Topic :: Scientific/Engineering :: Artificial Intelligence",
    #     "Topic :: Software Development :: Libraries :: Python Modules",
    # ],
    # python_requires=">=3.8",
    # install_requires=requirements,
    # extras_require={
    #     "dev": [
    #         "pytest>=7.0.0",
    #         "pytest-cov>=4.0.0",
    #         "black>=23.0.0",
    #         "isort>=5.12.0",
    #         "flake8>=6.0.0",
    #     ],
    #     "docs": [
    #         "sphinx>=7.0.0",
    #         "sphinx-rtd-theme>=1.3.0",
    #     ],
    # },
    # entry_points={
    #     "console_scripts": [
    #         "discussion-framework=graph_discussion.main:main",
    #     ],
    # },
    # include_package_data=True,
    # package_data={
    #     "graph_discussion": ["*.md", "*.txt", "*.example"],
    # },
    # keywords=[
    #     "ai",
    #     "multi-agent",
    #     "langgraph",
    #     "discussion",
    #     "collaboration",
    #     "decision-making",
    #     "llm",
    #     "openai",
    # ],
    # project_urls={
    #     "Documentation": "https://github.com/your-org/multi-agent-discussion-framework/docs",
    #     "Source": "https://github.com/your-org/multi-agent-discussion-framework",
    #     "Tracker": "https://github.com/your-org/multi-agent-discussion-framework/issues",
    # },
)
