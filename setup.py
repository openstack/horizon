#!/usr/bin/python
# Copyright (c) 2010-2011 OpenStack, LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import subprocess

from setuptools import setup, find_packages

cmdclass = {}

# If Sphinx is installed on the box running setup.py,
# enable setup.py to build the documentation, otherwise,
# just ignore it
try:
    from sphinx.setup_command import BuildDoc

    if 'DJANGO_SETTINGS_MODULE' not in os.environ:
        os.environ['DJANGO_SETTINGS_MODULE'] = 'local.local_settings'
    class local_BuildDoc(BuildDoc):
        def run(self):
            base_dir = os.path.dirname(os.path.abspath(__file__))
            subprocess.Popen(["python", "generate_autodoc_index.py"],
                             cwd=os.path.join(base_dir, "doc")).communicate()
            for builder in ['html']:  # ,'man'
                self.builder = builder
                self.finalize_options()
                BuildDoc.run(self)
    cmdclass['build_sphinx'] = local_BuildDoc

except:
    pass

setup(
    name='horizon',
    version='2011.3',
    description="OpenStack Dashboard",
    license='Apache License (2.0)',
    classifiers=["Programming Language :: Python"],
    keywords='dashboard openstack',
    author='OpenStack, LLC.',
    author_email='openstack@lists.launchpad.net',
    url='http://www.openstack.org',
    include_package_data=True,
    packages=find_packages(exclude=['test', 'bin']),
    scripts=[],
    zip_safe=False,
    cmdclass=cmdclass,
    install_requires=['setuptools'],
    test_suite='nose.collector',
    entry_points={},
    )
