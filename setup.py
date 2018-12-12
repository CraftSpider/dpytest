
import setuptools

with open("README.md", "r") as file:
    long_description = file.read()

setuptools.setup(
    name="dpytest",
    version="0.0.1",
    author="Rune Tynan",
    author_email="runetynan@gmail.com",
    description="A package that assists in writing tests for discord.py",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CraftSpider/dpytest",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 1 - Planning",
        "Topic :: Software Development :: Testing"
    ]
)
