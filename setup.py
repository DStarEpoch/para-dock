#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time   : 2025/3/7 11:02
# @Author : yuyeqing
# @File   : setup.py.py
# @IDE    : PyCharm
from setuptools import setup, find_packages

setup(
    name="para-dock",
    py_modules=["para-dock"],
    packages=find_packages(),
    version="0.0.1",
    install_requires=[
        "click",
        "pandas",
        "pyyaml",
        "tqdm",
        "vina",
        "openbabel-wheel",
        "numpy",
        "cython",
        "setuptools",
        "wheel",
    ],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'para-dock = main:dock_app'
        ]
    }
)