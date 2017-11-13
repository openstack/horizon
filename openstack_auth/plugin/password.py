# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging

from keystoneauth1.identity import v2 as v2_auth
from keystoneauth1.identity import v3 as v3_auth

from openstack_auth.plugin import base
from openstack_auth import utils

LOG = logging.getLogger(__name__)

__all__ = ['PasswordPlugin']


class PasswordPlugin(base.BasePlugin):
    """Authenticate against keystone given a username and password.

    This is the default login mechanism. Given a username and password inputted
    from a login form returns a v2 or v3 keystone Password plugin for
    authentication.
    """

    def get_plugin(self, auth_url=None, username=None, password=None,
                   user_domain_name=None, **kwargs):
        if not all((auth_url, username, password)):
            return None

        LOG.debug('Attempting to authenticate for %s', username)

        if utils.get_keystone_version() >= 3:
            return v3_auth.Password(auth_url=auth_url,
                                    username=username,
                                    password=password,
                                    user_domain_name=user_domain_name,
                                    unscoped=True)

        else:
            return v2_auth.Password(auth_url=auth_url,
                                    username=username,
                                    password=password)
