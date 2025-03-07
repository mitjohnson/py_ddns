from setuptools import setup, find_packages

setup(
    name = 'py_ddns',
    version= '0.1.0',
    author = 'Mitchell Johnson',
    license= 'MIT',
    author_email = '91237766+mitjohnson@users.noreply.github.com.',
    description = 'Simple programmable DDNS client to automate IP adress changes.',
    long_description = open('README.md').read(),
    long_description_content_type = 'text/markdown',
    url = 'https://github.com/mitjohnson/py_ddns',
    packages = find_packages(where='src'),
    classifiers = [
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    install_requires = ['cloudflare'],
    package_dir={'': 'ddns'},
)