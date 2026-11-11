from setuptools import setup, find_namespace_packages

setup(
    name='manus',
    version="0.1.0",
    python_requires=">=3.11",
    packages=['manus'] + [
        'manus.' + package for package in find_namespace_packages(include=["src", "src.*"])
    ],
    package_dir={'manus': "."},
    install_requires=['langgraph>=1.2.20,<1.3', 'langchain-core>=1.8,<2', 'openai>=3.49,<4', 'pydantic>=2.14,<3', 'tiktoken', 'toml', 'requests'],
)
