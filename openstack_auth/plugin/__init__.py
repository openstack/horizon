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

from openstack_auth.plugin.base import BasePlugin
from openstack_auth.plugin.k2k import K2KAuthPlugin
from openstack_auth.plugin.password import PasswordPlugin
from openstack_auth.plugin.token import TokenPlugin


__all__ = ['BasePlugin',
           'PasswordPlugin',
           'TokenPlugin',
           'K2KAuthPlugin']
