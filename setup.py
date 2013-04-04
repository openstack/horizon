#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os

from distutils.core import setup
from distutils.command.install import INSTALL_SCHEMES

from openstack_dashboard.openstack.common import setup as os_common_setup


requires = os_common_setup.parse_requirements()
depend_links = os_common_setup.parse_dependency_links()
tests_require = os_common_setup.parse_requirements(['tools/test-requires'])
project = 'horizon'

ROOT = os.path.dirname(__file__)
target_dirs = ['horizon', 'openstack_dashboard', 'bin']


def read(fname):
    return open(os.path.join(ROOT, fname)).read()


def split(path, result=None):
    """
    Split a path into components in a platform-neutral way.
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return split(head, [tail] + result)


# Tell distutils not to put the data_files in platform-specific installation
# locations. See here for an explanation:
# https://groups.google.com/forum/#!topic/comp.lang.python/Nex7L-026uw
for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
packages, data_files = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)

for target_dir in target_dirs:
    for dirpath, dirnames, filenames in os.walk(target_dir):
        # Ignore dirnames that start with '.'
        for i, dirname in enumerate(dirnames):
            if dirname.startswith('.'):
                del dirnames[i]
        if '__init__.py' in filenames:
            packages.append('.'.join(split(dirpath)))
        elif filenames:
            data_files.append([dirpath, [os.path.join(dirpath, f)
                               for f in filenames]])


setup(name=project,
      version=os_common_setup.get_version(project, '2013.1.1'),
      url='https://github.com/openstack/horizon/',
      license='Apache 2.0',
      description="The OpenStack Dashboard.",
      long_description=read('README.rst'),
      author='OpenStack',
      author_email='horizon@lists.launchpad.net',
      packages=packages,
      data_files=data_files,
      cmdclass=os_common_setup.get_cmdclass(),
      include_package_data=True,
      install_requires=requires,
      tests_require=tests_require,
      dependency_links=depend_links,
      zip_safe=False,
      classifiers=['Development Status :: 5 - Production/Stable',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: Apache Software License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Internet :: WWW/HTTP',
                   'Environment :: OpenStack']
)
