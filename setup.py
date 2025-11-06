"""Setup configuration for agentshield package."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agentshield",
    version="0.1.0",
    author="AgentShield",
    author_email="support@agent-shield.com",
    description="Security and monitoring for AI agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://agent-shield.com",
    project_urls={
        "Documentation": "https://agent-shield.com/docs",
        "Source": "https://github.com/agentshield/python-sdk",
        "Bug Reports": "https://github.com/agentshield/python-sdk/issues",
        "Dashboard": "https://agent-shield.com/dashboard",
    },
    packages=find_packages(exclude=["tests", "tests.*", "examples", "examples.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.28.0",
        "urllib3>=1.26.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.990",
            "types-requests>=2.28.0",
        ],
        "langchain": [
            "langchain>=0.1.0",
        ],
    },
    keywords="ai agent security monitoring llm safety policy enforcement",
    license="MIT",
    zip_safe=False,
    include_package_data=True,
)
