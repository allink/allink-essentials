#! /usr/bin/env python
import os
from setuptools import setup

import allink_essentials
setup(
    name='allink_essentials',
    version=allink_essentials.__version__,
    description='django based newsletter toolkit',
    long_description=open(os.path.join(os.path.dirname(__file__), 'README.rst')).read(),
    author='Marc Egli',
    author_email='egli@allink.ch',
    url='http://github.com/allink/allink-essentials/',
    license='BSD License',
    platforms=['OS Independent'],
    packages=[
        'allink_essentials',
        'allink_essentials.fabfiles',
    ],
    # package_data={'allink_essentials':'templates/*.html'},
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Communications :: Email',
    ],
    requires=[
    ],
    include_package_data=True,
)
