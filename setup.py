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
import re
from setuptools import setup, find_packages
from horizon import version


ROOT = os.path.dirname(__file__)
PIP_REQUIRES = os.path.join(ROOT, "tools", "pip-requires")
TEST_REQUIRES = os.path.join(ROOT, "tools", "test-requires")


def parse_requirements(*filenames):
    """
    We generate our install_requires from the pip-requires and test-requires
    files so that we don't have to maintain the dependency definitions in
    two places.
    """
    requirements = []
    for f in filenames:
        for line in open(f, 'r').read().split('\n'):
            # Comment lines. Skip.
            if re.match(r'(\s*#)|(\s*$)', line):
                continue
            # Editable matches. Put the egg name into our reqs list.
            if re.match(r'\s*-e\s+', line):
                pkg = re.sub(r'\s*-e\s+.*#egg=(.*)$', r'\1', line)
                requirements.append("%s" % pkg)
            # File-based installs not supported/needed. Skip.
            elif re.match(r'\s*-f\s+', line):
                pass
            else:
                requirements.append(line)
    return requirements


def parse_dependency_links(*filenames):
    """
    We generate our dependency_links from the pip-requires and test-requires
    files for the dependencies pulled from github (prepended with -e).
    """
    dependency_links = []
    for f in filenames:
        for line in open(f, 'r').read().split('\n'):
            if re.match(r'\s*-[ef]\s+', line):
                line = re.sub(r'\s*-[ef]\s+', '', line)
                line = re.sub(r'\s*git\+https', 'http', line)
                line = re.sub(r'\.git#', '/tarball/master#', line)
                dependency_links.append(line)
    return dependency_links


def read(fname):
    return open(os.path.join(ROOT, fname)).read()


setup(name="horizon",
      version=version.canonical_version_string(),
      url='https://github.com/openstack/horizon/',
      license='Apache 2.0',
      description="The OpenStack Dashboard.",
      long_description=read('README.rst'),
      author='OpenStack',
      author_email='horizon@lists.launchpad.net',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=parse_requirements(PIP_REQUIRES),
      tests_require=parse_requirements(TEST_REQUIRES),
      dependency_links=parse_dependency_links(PIP_REQUIRES, TEST_REQUIRES),
      classifiers=['Development Status :: 4 - Beta',
                   'Framework :: Django',
                   'Intended Audience :: Developers',
                   'License :: OSI Approved :: Apache Software License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Topic :: Internet :: WWW/HTTP']
)
