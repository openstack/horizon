#!/usr/bin/env python

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
import sys

import django
from django.test.runner import DiscoverRunner as test_runner


os.environ['DJANGO_SETTINGS_MODULE'] = 'openstack_auth.tests.settings'

if hasattr(django, 'setup'):
    django.setup()


def run(*test_args):
    if not test_args:
        test_args = ['tests']
    parent = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
    )
    sys.path.insert(0, parent)
    failures = test_runner().run_tests(test_args)
    sys.exit(failures)


if __name__ == '__main__':
    run(*sys.argv[1:])
