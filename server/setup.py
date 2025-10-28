from setuptools import setup, find_packages

setup(
    name="server",
    packages=find_packages(where="app"),
    package_dir={"": "app"},
    include_package_data=True,
    zip_safe=False,
)