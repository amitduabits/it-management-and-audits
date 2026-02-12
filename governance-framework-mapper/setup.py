from setuptools import setup, find_packages

setup(
    name="governance-framework-mapper",
    version="1.0.0",
    description="Map organizational IT processes to COBIT 2019 and ITIL v4 governance frameworks",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Dr Amit Dua",
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "click>=8.0",
        "jinja2>=3.1",
        "rich>=13.0",
    ],
    entry_points={
        "console_scripts": [
            "gfm=src.cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Topic :: System :: Systems Administration",
    ],
)
