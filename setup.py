"""
Setup.py

Build proccess for package.
"""
from setuptools import setup, find_packages

def readme() -> str:
    """ Gets readme """
    with open('README.md', 'r', encoding='utf-8') as f:
        return f.read()

setup(
    name = 'pyddns',
    version= '0.1.0',
    author = 'Mitchell Johnson',
    license= 'MIT',
    author_email = '91237766+mitjohnson@users.noreply.github.com.',
    description = 'Simple programmable DDNS client to automate IP adress changes.',
    long_description = readme(),
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/mitjohnson/py_ddns',
    package_dir={'': 'src'},
    packages = find_packages(where='src'),
    classifiers = [
        'License :: OSI Approved :: MIT License'
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    install_requires = ['cloudflare'],
    python_requires=">=3.10",
)
