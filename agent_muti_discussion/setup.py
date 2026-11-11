from setuptools import setup, find_namespace_packages

setup(
    name='agent_muti_discussion',
    version="0.1.0",
    python_requires=">=3.11",
    packages=['agent_muti_discussion'] + [
        'agent_muti_discussion.' + package for package in find_namespace_packages(include=["src", "src.*"])
    ],
    package_dir={'agent_muti_discussion': "."},
    install_requires=['openai>=3.49,<4', 'langchain-core>=1.8,<2', 'python-dotenv', 'PyYAML', 'requests'],
)
