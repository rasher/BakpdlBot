#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
        'Click~=7.0',
        'discord.py~=2.1.0',
        'python-dotenv~=0.19.2',
        'google-api-python-client~=1.12.8',
        'google-auth-oauthlib~=0.4.1',
        'oauth2client~=4.1.3',
        'tabulate~=0.8.9',
        'ago~=0.0.93',
        'requests~=2.25.1',
        'pendulum~=2.1.2',
        'requests-cache~=0.7.2',
        'demjson~=2.2.4',
        'requests-html~=0.6.6',
        'matplotlib~=3.5.1',
        'jinja2~=3.0.3',
        'appdirs~=1.4.4',
        ]

test_requirements = [ ]

setup(
    author="Mick Boekhoff",
    author_email='mickboekhoff@hotmail.com',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Bot to help manage the Discord server for Backpedal cc.",
    entry_points={
        'console_scripts': [
            'bakpdlbot=bakpdlbot.cli:main',
            'riderlist=bakpdlbot.riderlist:main',
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
