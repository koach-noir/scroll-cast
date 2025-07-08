from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="scroll-cast",
    version="1.0.0",
    author="scroll-cast Team",
    author_email="contact@scroll-cast.dev",
    description="Pure text animation generation system for creating engaging, readable content",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/koach-noir/scroll-cast",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Video",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "scroll-cast=scrollcast.orchestrator.cli.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "scrollcast": [
            "templates/**/*",
            "config/*.yaml",
        ],
    },
)