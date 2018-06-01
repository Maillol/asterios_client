from setuptools import setup

import os
import sys
sys.path.insert(0, os.path.join(os.path.curdir, 'asterios_client'))

from __version__ import __version__


if 'a' in __version__:
    development_status = 'Development Status :: 3 - Alpha'
elif 'b' in __version__:
    development_status = 'Development Status :: 4 - Beta'
else:
    development_status = 'Development Status :: 5 - Production/Stable'


setup(
    name='asterios',
    version=__version__,
    description='Asterios client',
    keywords='escape game server Asterios client',
    author='Vincent Maillol',
    author_email='vincent.maillol@gmail.com',
    url='https://github.com/maillol/asterios_client',
    license='GPLv3',
    packages=['asterios_client'],
    classifiers=[
        development_status,
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)'
    ],
    python_requires='>=3.5'
)
