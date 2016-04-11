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

from django.conf import settings

from horizon.utils.memoized import memoized  # noqa


class IdentityMixIn(object):
    @memoized
    def get_admin_roles(self):
        _admin_roles = [role.lower() for role in getattr(
            settings,
            'OPENSTACK_KEYSTONE_ADMIN_ROLES',
            ['admin'])]
        return _admin_roles
