import contextlib
import os
import shutil
import subprocess
import webbrowser
from itertools import chain
from pathlib import Path
from platform import uname

from invoke import task

"""'Makefile' equivalent for invoke tool (invoke or inv).
# Installation
`pip install invoke`
# Usage
> inv test
> inv build
etc...
# Autocompletion
For auto completion, just run:
`source <(inv --print-completion-script bash)`
or
`source <(inv --print-completion-script zsh)`
(or add it to ~/.zshrc or ~/.bashrc)
"""


# UTILS -----------------------------------------------------------------------

def get_platform():
    """Check the platform (Windos, Linux, or WSL)."""
    u = uname()
    if u.system == 'Windows':
        return 'windows'
    elif u.system == 'Linux' and 'microsoft' in u.release:
        return 'wsl'
    else:
        return 'linux'


def get_index_path():
    """Get full path for ./htmlcov/index.html file."""
    platform = get_platform()
    if platform != "wsl":
        return Path('.').resolve() / 'htmlcov' / 'index.html'
    # TODO: this part with .strip().replace() is ugly...
    process = subprocess.run(['wslpath', '-w', '.'], capture_output=True, text=True)
    pathstr = process.stdout.strip().replace('\\', '/')
    return Path(pathstr) / 'htmlcov/index.html'


# TASKS------------------------------------------------------------------------

@task
def lint(c):
    """flake8 - static check for python files"""
    c.run("flake8 discord/ext/test tests/ tasks.py")


@task
def cleantest(c):
    """Clean artifacts like *.pyc, __pycache__, .pytest_cache, etc..."""
    # Find .pyc or .pyo files and delete them
    exclude = ('venv', '.venv')
    p = Path('.')
    genpyc = (i for i in p.glob('**/*.pyc') if not str(i.parent).startswith(exclude))
    genpyo = (i for i in p.glob('**/*.pyo') if not str(i.parent).startswith(exclude))
    artifacts = chain(genpyc, genpyo)
    for art in artifacts:
        os.remove(art)

    # Delete caches folders
    cache1 = (i for i in p.glob('**/__pycache__') if not str(i.parent).startswith(exclude))
    cache2 = (i for i in p.glob('**/.pytest_cache') if not str(i.parent).startswith(exclude))
    cache3 = (i for i in p.glob('**/.mypy_cache') if not str(i.parent).startswith(exclude))
    caches = chain(cache1, cache2, cache3)
    for cache in caches:
        shutil.rmtree(cache)

    # Delete coverage artifacts
    with contextlib.suppress(FileNotFoundError):
        os.remove('.coverage')
        shutil.rmtree('htmlcov')


@task
def cleanbuild(c):
    """Clean dist/, build/ and egg-info/."""
    exclude = ('venv', '.venv')
    p = Path('.')
    gen1 = (i for i in p.glob('**/dist') if not str(i.parent).startswith(exclude))
    gen2 = (i for i in p.glob('**/build') if not str(i.parent).startswith(exclude))
    gen3 = (i for i in p.glob('**/*.egg-info') if not str(i.parent).startswith(exclude))
    builds = chain(gen1, gen2, gen3)
    for b in builds:
        shutil.rmtree(b)


@task
def cleandoc(c):
    """Clean the documentation build directory."""
    with contextlib.suppress(FileNotFoundError):
        shutil.rmtree(Path('.') / 'docs' / '_build')


@task(cleantest, cleanbuild)
def clean(c):
    """Equivalent to both cleanbuild and cleantest..."""
    pass


@task
def test(c):
    """Run tests with pytest."""
    c.run("pytest tests/")


@task
def coverage(c):
    """Run unit-tests using pytest, with coverage reporting."""
    # use the browser defined in varenv $BROWSER
    # in WSL, if not set, example :  export BROWSER='/mnt/c/Program Files/Google/Chrome/Application/chrome.exe'
    path = get_index_path()
    c.run('coverage run --source=discord/ext/test -m pytest')
    c.run('coverage report -m')
    c.run('coverage html')
    webbrowser.open(path.as_uri())


@task(cleanbuild)
def build(c):
    """Build package using python -m build."""
    c.run('python -m build')


@task(cleandoc)
def doc(c):
    """Make the documentation (html)"""
    c.run('cd docs && make html')
    path = Path('.') / 'docs' / '_build' / 'html' / 'index.html'
    webbrowser.open(path.resolve().as_uri())


@task(cleanbuild)
def release(c, version="patch"):
    """Build and release. Optional parameter is "patch (default) / version=minor / version=major"""  # noqa: E501
    c.run(f"bump2version {version}")
    c.run('python -m build')
    c.run("git push")
    c.run("git push --tags")
    c.run("twine upload --config-file .pypirc dist/*")
