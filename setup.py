from setuptools import setup, find_packages

setup(
    name="uniland",
    version="2.2.0",
    description="UniLand — a small, friendly scripting language",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="UniLand",
    packages=find_packages(),
    # The interpreter core runs on the standard library alone (so
    # `python -m uniland` works without installing anything). Pillow is a
    # convenience default so images "just work" in the GUI across all formats;
    # video and http are optional extras.
    install_requires=["Pillow"],
    extras_require={
        "http": ["requests"],
        "video": ["imageio", "imageio-ffmpeg"],
        "all": ["requests", "imageio", "imageio-ffmpeg"],
    },
    entry_points={
        "console_scripts": [
            "uniland=uniland.cli:main",
        ],
    },
    python_requires=">=3.10",
)
