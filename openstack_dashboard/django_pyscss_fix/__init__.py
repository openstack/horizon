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

import logging
import os
import sys

import django
import six
import six.moves

from django.conf import settings
from scss.grammar.expression import SassExpressionScanner

# Temporary workaround for a situation that django-pyscss depends on
# a vendored version of six, django.utils.six which was dropped in Django 3.0.
# TODO(amotoki): Drop the workaround once django-pyscss supports Django 3.0+.
if django.VERSION[0] >= 3:
    sys.modules['django.utils.six'] = six
    sys.modules['django.utils.six.moves'] = six.moves

scss_asset_root = os.path.join(settings.STATIC_ROOT, 'scss', 'assets')
LOG = logging.getLogger(__name__)

"""
This is a workaround for https://bugs.launchpad.net/horizon/+bug/1367590
It works by creating a path that django_scss will attempt to create
later if it doesn't exist. The django_pyscss code fails
intermittently because of concurrency issues.  This code ignores the
exception and if it was anything other than the concurrency issue
django_pyscss will discover the problem later.

TODO (doug-fish):  remove this workaround once fix for
https://github.com/fusionbox/django-pyscss/issues/23 is picked up.
"""
try:
    if not os.path.exists(scss_asset_root):
        os.makedirs(scss_asset_root)
except Exception as e:
    LOG.info("Error precreating path %(root)s, %(exc)s",
             {'root': scss_asset_root, 'exc': e})

# Fix a syntax error in regular expression, where a flag is not at the
# beginning of the expression.
# This is fixed upstream at
# https://github.com/Kronuz/pyScss/commit
# /73559d047706ccd4593cf6aa092de71f35164723
# We should remove it once we use that version.

for index, (name, value) in enumerate(SassExpressionScanner._patterns):
    if name == 'OPACITY':
        SassExpressionScanner._patterns[index] = ('OPACITY', '(?i)(opacity)')
