import os
from setuptools import setup, find_packages, findall

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "openstack-dashboard",
    version = "0.2",
    url = 'https://github.com/cloudbuilders/openstack-dashboard.git',
    license = 'Apache 2.0',
    description = "A Django interface for OpenStack.",
    long_description = read('README'),
    author = 'Devin Carlen',
    author_email = 'devin.carlen@gmail.com',
    packages = find_packages(),
    package_data = {'django_openstack':
                        [s[len('django_openstack/'):] for s in
                         findall('django_openstack/templates')]},
    install_requires = ['setuptools', 'mox>=0.5.0'],
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

