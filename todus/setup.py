from setuptools import setup, find_packages

setup(
    name="todus-lib",
    version="1.2.0",
    description="Cliente Python para ToDus (mensajería cubana)",
    author="OrionWolf",
    packages=find_packages(),
    install_requires=["requests"],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
