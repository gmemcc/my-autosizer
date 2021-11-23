# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="myautoresizer",
    version="0.1.8-ubuntu-20",
    packages=find_packages(exclude=["tests"]),
    package_data={
        'myautoresizer': ['*.ini'],
    },
    entry_points={
        'console_scripts': [
            'ma_printrect = myautoresizer.scripts:ma_printrect',
            'ma_autoresize = myautoresizer.scripts:ma_autoresize',
            'ma_autoresize_active = myautoresizer.scripts:ma_autoresize_active',
        ],
    },
    description='Automatically resize and move GDK windows according to the configuration file',
    author='Alex Wong',
    author_email='alex@gmem.cc',
    url='https://github.com/seinohitomi/my-autoresizer'
)
