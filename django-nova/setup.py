import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "django-nova",
    version = "0.1",
    url = 'https://launchpad.net/django-nova/',
    license = 'Apache 2.0',
    description = "A Django interface for OpenStack Nova.",
    long_description = read('README'),
    author = 'Devin Carlen',
    author_email = 'devin.carlen@gmail.com',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    install_requires = ['setuptools', 'boto==1.9b', 'mox>=0.5.0',
                        'nova-adminclient'],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)

