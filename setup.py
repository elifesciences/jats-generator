"module setup script"
from setuptools import setup

import jatsgenerator

with open('README.rst') as fp:
    README = fp.read()

setup(
    name='jatsgenerator',
    version=jatsgenerator.__version__,
    description='JATS XML generator.',
    long_description=README,
    packages=['jatsgenerator'],
    license='MIT',
    install_requires=[
        "elifetools",
        "elifearticle",
        "ejpcsvparser",
        "GitPython",
        "configparser"
    ],
    url='https://github.com/elifesciences/jats-generator',
    maintainer='eLife Sciences Publications Ltd.',
    maintainer_email='tech-team@elifesciences.org',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        ]
    )
