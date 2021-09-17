# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import sys

import django
import six
import six.moves

# Temporary workaround for a situation that django-pyscss depends on
# a vendored version of six, django.utils.six which was dropped in Django 3.0.
# TODO(amotoki): Drop the workaround once django-pyscss supports Django 3.0+.
if django.VERSION[0] >= 3:
    sys.modules['django.utils.six'] = six
    sys.modules['django.utils.six.moves'] = six.moves
