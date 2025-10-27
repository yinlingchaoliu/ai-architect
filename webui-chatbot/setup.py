from setuptools import setup, find_packages

setup(
    name="chatbot",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
)