from setuptools import setup, find_namespace_packages

setup(
    name='mcp_client_manager',
    version="0.1.0",
    python_requires=">=3.11",
    packages=['mcp_client_manager'] + [
        'mcp_client_manager.' + package for package in find_namespace_packages(include=["src", "src.*"])
    ],
    package_dir={'mcp_client_manager': "."},
    install_requires=['fastmcp>=4.1.8,<5', 'mcp>=2.3,<3', 'openai>=3.49,<4', 'python-dotenv'],
)
