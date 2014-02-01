from distutils.core import setup

setup(
    name='stash',
    version='0.0.1',
    author='Alexander Davydov',
    author_email='nyddle@gmail..com',
    packages=['stash' ],
    scripts=[ 'bin/stash.py' ],
    url='http://pypi.python.org/pypi/pystash/',
    license='LICENSE.txt',
    description='Save your code snippets in the cloud.',
    long_description=open('README.txt').read(),
    install_requires=[
    ],
)
