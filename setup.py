"module setup script"
from setuptools import setup

import jatsgenerator

with open("README.md") as fp:
    README = fp.read()

setup(
    name="jatsgenerator",
    version=jatsgenerator.__version__,
    description="JATS XML generator.",
    long_description=README,
    long_description_content_type="text/markdown",
    packages=["jatsgenerator"],
    license="MIT",
    install_requires=[
        "elifetools>=0.33.0",
        "elifearticle>=0.16.0",
        "ejpcsvparser>=0.3.0",
        "GitPython",
        "configparser",
    ],
    url="https://github.com/elifesciences/jats-generator",
    maintainer="eLife Sciences Publications Ltd.",
    maintainer_email="tech-team@elifesciences.org",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
