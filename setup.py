from __future__ import unicode_literals

from setuptools import find_packages, setup

setup(
    name="djangogcal",
    packages=find_packages(),
    install_requires=['django>=1.6', 'google-api-python-client', 'requests', 'oauth2client'],
    version="0.2.2",
    description=(
        "Django application allowing developers to synchronize instances of their models with Google Calendar."
    ),
    author="Incuna Ltd",
    author_email="admin@incuna.com",
    url="http://incuna.com/",
)
