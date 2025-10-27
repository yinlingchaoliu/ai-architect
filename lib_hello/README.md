# Hello SDK

一个简单的 Python SDK 示例，用于生成多语言问候语。

## 安装

```bash
pip install -e /path/to/hello
```

### 查看包的位置
```shell
pip show hello-sdk
```


### 构建包
```shell
# 构建源码包和wheel包
python -m build

# 只构建wheel包
python setup.py bdist_wheel
```

### 发布到 PyPI

```shell
# 测试发布到 TestPyPI
twine upload --repository testpypi dist/*

# 正式发布到 PyPI
twine upload dist/*
```

### 安装本地 Wheel
```shell
pip install dist/hello_sdk-0.1.0-py3-none-any.whl
```

### 发布到私有 PyPI 服务器
```shell
twine upload --repository-url https://your-pypi-server.com dist/*
```