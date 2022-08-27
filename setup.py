import os

from setuptools import find_packages, setup

from taskmonitor import __version__

with open(os.path.join(os.path.dirname(__file__), "README.md")) as readme:
    README = readme.read()

os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="aa-taskmonitor",
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    license="MIT",
    description="Alliance Auth plugin for monitoring celery tasks",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://gitlab.com/ErikKalkoken/aa-taskmonitor",
    author="Erik Kalkoken",
    author_email="kalkoken87@gmail.com",
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires="~=3.8",
    install_requires=[
        "allianceauth>=2.9",
        "allianceauth-app-utils>=1.14.2",
    ],
)
