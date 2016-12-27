import os
from os.path import abspath, dirname, join
from setuptools import setup, find_packages

__version__ = None

# Allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

# Get proper long description for package
current_dir = dirname(abspath(__file__))
description = open(join(current_dir, "README.rst")).read()
changes = open(join(current_dir, "CHANGES.rst")).read()
long_description = '\n\n'.join([description, changes])
exec(open(join(current_dir, "pierky/ipdetailscache/version.py")).read())

# Get the long description from README.md
setup(
    name="ipdetailscache",
    version=__version__,

    packages=["pierky", "pierky.ipdetailscache"],
    namespace_packages=["pierky"],
    include_package_data=True,

    license="MIT",
    description="A Python library to gather IP address details (ASN, prefix, resource holder, reverse DNS) using the RIPEStat API",
    long_description=long_description,
    url="https://github.com/pierky/ipdetailscache",
    download_url="https://github.com/pierky/ipdetailscache",

    author="Pier Carlo Chiodi",
    author_email="pierky@pierky.com",
    maintainer="Pier Carlo Chiodi",
    maintainer_email="pierky@pierky.com",

    install_requires=[
        "IPy>=0.83",
    ],
    tests_require=[
        "nose",
        "coverage",
        "mock",
    ],
    test_suite="nose.collector",

    keywords=['RIPE', 'RIPE NCC', 'RIPE Stat', 'Library', 'IPv4', 'IPv6', 'IP address'],

    classifiers=[
        "Development Status :: 4 - Beta",

        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",

        "License :: OSI Approved :: MIT License",

        "Operating System :: POSIX",
        "Operating System :: Unix",

        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",

        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: System :: Networking",
    ],
)
