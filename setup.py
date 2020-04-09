
import setuptools
import re

with open("discord/ext/test/__init__.py", "r") as file:
    try:
        version = re.search(r"^__version__\s*=\s*[\"']([^\"']*)[\"']", file.read(), re.MULTILINE).group(1)
    except Exception as e:
        raise RuntimeError("Version isn't set")

if version.endswith(("a", "b")):
    try:
        import subprocess as sp
        p = sp.Popen(["git", "rev-list", "--count", "HEAD"], stdout=sp.PIPE, stderr=sp.PIPE)
        out, err = p.communicate()
        if out:
            version += out.decode("utf-8").strip()
        p = sp.Popen(["git", "rev-parse", "--short", "HEAD"], stdout=sp.PIPE, stderr=sp.PIPE)
        out, err = p.communicate()
        if out:
            version += "+g" + out.decode("utf-8").strip()
    except Exception as e:
        raise RuntimeError("Failure to get current git commit")

with open("README.md", "r") as file:
    long_description = file.read()

setuptools.setup(
    name="dpytest",
    version=version,
    author="Rune Tynan",
    author_email="runetynan@gmail.com",
    description="A package that assists in writing tests for discord.py",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/CraftSpider/dpytest",
    packages=["discord.ext.test"],
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Topic :: Software Development :: Testing"
    ],
    keywords="discord discord.py test",
    install_requires=["discord.py", "pytest-asyncio"]
)
