#!/bin/bash
# publish.sh

set -e

# 清理旧构建
rm -rf dist/ build/ *.egg-info/

# 运行测试
#pytest

# 代码质量检查
#flake8 src/
#black --check src/

# 发布到选择的平台
if [ "$1" = "pypi" ]; then
    # 构建包
    python -m build
    twine upload dist/*
elif [ "$1" = "testpypi" ]; then
    # 构建包
    python -m build
    twine upload --repository testpypi dist/*
elif [ "$1" = "internal" ]; then
    # 构建包
    python -m build
    # 复制到内部服务器
    scp dist/* user@internal-server:/path/to/packages/
elif [ "$1" = "local" ]; then
    pip install -e . --force-reinstall
else
    echo "Usage: $0 [pypi|testpypi|internal|local]"
fi