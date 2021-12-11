#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = ['Click>=7.0', ]

test_requirements = [ ]

setup(
    author="Mick Boekhoff",
    author_email='mickboekhoff@hotmail.com',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Bot to help manage the Discord server for Backpedal cc.",
    entry_points={
        'console_scripts': [
            'bakpdlbot=bakpdlbot.cli:main',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='bakpdlbot',
    name='bakpdlbot',
    packages=find_packages(include=['bakpdlbot', 'bakpdlbot.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/mickboekhoff/bakpdlbot',
    version='0.1.0',
    zip_safe=False,
)
