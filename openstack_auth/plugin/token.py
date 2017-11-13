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

from keystoneauth1.identity import v2 as v2_auth
from keystoneauth1.identity import v3 as v3_auth

from openstack_auth.plugin import base
from openstack_auth import utils


__all__ = ['TokenPlugin']


class TokenPlugin(base.BasePlugin):
    """Authenticate against keystone with an existing token."""

    def get_plugin(self, auth_url=None, token=None, project_id=None,
                   **kwargs):
        if not all((auth_url, token)):
            return None

        if utils.get_keystone_version() >= 3:
            return v3_auth.Token(auth_url=auth_url,
                                 token=token,
                                 project_id=project_id,
                                 reauthenticate=False)

        else:
            return v2_auth.Token(auth_url=auth_url,
                                 token=token,
                                 tenant_id=project_id,
                                 reauthenticate=False)
