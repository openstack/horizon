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

from django.conf import settings

scss_asset_root = os.path.join(settings.STATIC_ROOT, 'scss', 'assets')
LOG = logging.getLogger(__name__)

"""
This is a workaround for https://bugs.launchpad.net/horizon/+bug/1367590
It works by creating a path that django_scss will attempt to create
later if it doesn't exist. The django_pyscss code fails
intermittantly because of concurrency issues.  This code ignores the
exception and if it was anything other than the concurrency issue
django_pyscss will discover the problem later.

TODO (doug-fish):  remove this workaround once fix for
https://github.com/fusionbox/django-pyscss/issues/23 is picked up.
"""
try:
    if not os.path.exists(scss_asset_root):
        os.makedirs(scss_asset_root)
except Exception as e:
    LOG.info("Error precreating path %s, %s" % (scss_asset_root, e))
