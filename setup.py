# coding=UTF-8
from distutils.core import setup

from setuptools import find_packages

setup(
    name='parides',
    version='0.4',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    url='https://github.com/goettl79/parides',
    download_url='https://github.com/goettl79/parides/archive/0.4.tar.gz',
    license='Apache',
    author='Georg Öttl',
    keywords=['monitoring', 'prometheus'],  # arbitrary keywords
    author_email='georg.oettl@gmail.com',
    description='Parides is a simple module to convert Prometheus metrics data to a panda dataframe or a '
                'comma-separated file.',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
    ],
    entry_points = {
        'console_scripts': ['parides = parides.cli:main'],
    }
)
