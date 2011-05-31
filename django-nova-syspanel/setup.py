import os
from setuptools import setup, find_packages, findall

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "django-nova-syspanel",
    version = "0.1",
    url = 'https://launchpad.net/openstack-dashboard/',
    license = 'Apache 2.0',
    description = "A Django interface for OpenStack Nova.",
    long_description = read('README'),
    author = 'Todd Willey',
    author_email = 'xtoddx@gmail.com',
    packages = find_packages('src'),
    package_dir = {'': 'src'},
    package_data = {'django_nova_syspanel':
                        [s[len('src/django_nova_syspanel/'):] for s in
                         findall('src/django_nova_syspanel/templates')]},
    install_requires = ['setuptools', 'boto==1.9b', 'mox>=0.5.0'],
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

