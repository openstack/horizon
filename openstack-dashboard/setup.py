import os
import shutil
from setuptools import setup, find_packages, findall

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

dst = 'debian/openstack-dashboard/var/lib/dash'
os.system('rm -rf %s' % dst)
shutil.copytree('media', '%s/media' % dst)
shutil.copytree('tools', '%s/tools' % dst)
shutil.copytree('dashboard', '%s/dashboard' % dst)
shutil.copytree('local', '%s/local' % dst)


setup(
    name = "openstack-dashboard",
    version = "0.2",
    url = 'https://github.com/cloudbuilders/openstack-dashboard.git',
    license = 'Apache 2.0',
    description = "A Django interface for OpenStack.",
    long_description = read('README'),
    author = 'Devin Carlen',
    author_email = 'devin.carlen@gmail.com',
#    packages = find_packages(),
#    package_data = {'openstack-dashboard':
#                        [s[len('dashboard/'):] for s in
#                         findall('dashboard/templates')]},

    data_files = [],
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

