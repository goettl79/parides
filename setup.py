from distutils.core import setup

from setuptools import find_packages

setup(
    name='parides',
    version='1.0',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    url='',
    license='Apache',
    author='Georg Öttl',
    author_email='georg.oettl@gmail.com',
    description='',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3',
    ],
)
