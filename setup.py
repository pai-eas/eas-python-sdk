#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='eas-prediction',
    version='0.2',
    description='Python client sdk for eas inference service',
    url='http://gitlab.alibaba-inc.com/eas/eas-python-sdk',
    packages=['eas_prediction'],
    install_requires=['urllib3','protobuf'])
