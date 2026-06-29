from setuptools import setup, find_packages

setup(
    name="uniland",
    version="2.1.0",
    description="UniLand — a small, friendly scripting language",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="UniLand",
    packages=find_packages(),
    # The core has zero dependencies. `requests` is only needed for the
    # http_* functions, and tkinter (GUI) ships with Python.
    install_requires=[],
    extras_require={"http": ["requests"]},
    entry_points={
        "console_scripts": [
            "uniland=uniland.cli:main",
        ],
    },
    python_requires=">=3.10",
)
