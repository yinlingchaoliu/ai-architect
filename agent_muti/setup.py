from setuptools import setup, find_namespace_packages

setup(
    name='mutiagent',
    version="0.1.0",
    python_requires=">=3.11",
    packages=['agent_muti'] + [
        'agent_muti.' + package for package in find_namespace_packages(include=["src", "src.*"])
    ],
    package_dir={'agent_muti': "."},
    install_requires=['openai>=3.49,<4', 'python-dotenv', 'PyYAML'],
)
