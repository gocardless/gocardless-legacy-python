from setuptools import setup, find_packages
import os

DESCRIPTION = "The Python client library for the GoCardless API"

LONG_DESCRIPTION = None
try:
    LONG_DESCRIPTION = open('README.md').read()
except:
    pass

# Dirty hack to get version number from __init__.py - we can't import it as it
# depends on requests and requests isn't installed until this file is read
init = os.path.join(os.path.dirname(__file__), 'gocardless', '__init__.py')
version_line = [line for line in open(init) if line.startswith("VERSION")][0]
version = '.'.join(str(p) for p in eval(version_line.split('=')[-1]))

CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

setup(
    name='gocardless',
    version=version,
    packages=find_packages(),
    author='GoCardless',
    author_email='developers@{nospam}gocardless.com',
    url='https://gocardless.com/docs/python/merchant_client_guide',
    license='MIT',
    include_package_data=True,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    platforms=['any'],
    classifiers=CLASSIFIERS,
    install_requires=['requests>=1.0.0', 'six>=1.9.0'],
    test_suite='test',
)
