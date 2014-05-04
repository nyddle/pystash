from distutils.core import setup

setup(
    name='stash',
    version='0.0.5',
    author='Alexander Davydov',
    author_email='nyddle@gmail.com',
    packages=['stash' ],
    scripts=[ 'bin/stash' ],
    url='http://pypi.python.org/pypi/pystash/',
    license='LICENSE.txt',
    description='Save your code snippets in the cloud.',
    long_description=open('README.rst').read(),
    install_requires=[
        "args>=0.1.0",
        "clint>=0.3.3",
        "requests>=2.2.0",
        "wsgiref>=0.1.2"
    ],
)
