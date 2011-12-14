# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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
from setuptools import setup, find_packages, findall
from horizon import version

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "horizon",
    version = version.canonical_version_string(),
    url = 'https://github.com/openstack/horizon/',
    license = 'Apache 2.0',
    description = "A Django interface for OpenStack.",
    long_description = read('README'),
    author = 'Devin Carlen',
    author_email = 'devin.carlen@gmail.com',
    packages = find_packages(),
    package_data = {'horizon':
                        [s[len('horizon/'):] for s in
                         findall('horizon/templates') \
                             + findall('horizon/dashboards/nova/templates') \
                             + findall('horizon/dashboards/syspanel/templates') \
                             + findall('horizon/dashboards/settings/templates')]},
    install_requires = ['setuptools', 'mox>=0.5.3', 'django_nose'],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
    ]
)
