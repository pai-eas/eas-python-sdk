#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

setup(
    name='eas-prediction',
    version='0.31',
    description='Python client sdk for eas inference service',
    url='http://gitlab.alibaba-inc.com/eas/eas-python-sdk',
    packages=['eas_prediction', 'eas_prediction/queue_types'],
    install_requires=['urllib3', 'protobuf>=3.14.0, <=3.20.3', 'numpy>=1.9', 'websocket-client','python-snappy'])
