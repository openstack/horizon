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

import logging

from keystoneauth1.identity import v3 as v3_auth

from openstack_auth.plugin import base

LOG = logging.getLogger(__name__)

__all__ = ['TotpPlugin']


class TotpPlugin(base.BasePlugin):

    def get_plugin(self, auth_url=None, username=None, passcode=None,
                   user_domain_name=None, receipt=None, **kwargs):
        if not all((auth_url, username, passcode, user_domain_name, receipt)):
            return None
        LOG.debug('Attempting to authenticate with time-based one time'
                  ' password for %s', username)

        auth = v3_auth.TOTP(
            auth_url=auth_url,
            username=username,
            passcode=passcode,
            user_domain_name=user_domain_name,
            unscoped=True
        )
        auth.add_method(v3_auth.ReceiptMethod(receipt=receipt))

        return auth
