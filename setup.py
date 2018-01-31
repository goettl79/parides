# coding=UTF-8
from distutils.core import setup

from setuptools import find_packages

setup(
    name='parides',
    version='0.1',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    url='https://github.com/goettl79/parides',
    download_url='https://github.com/goettl79/parides/archive/0.1.tar.gz',
    license='Apache',
    author='Georg Öttl',
    keywords=['monitoring', 'prometheus'], # arbitrary keywords
    author_email='georg.oettl@gmail.com',
    description='Parides is a simple python module to convert Prometheus metrics data to a panda frame or a '
                'comma-separated file.',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
    ],
)
