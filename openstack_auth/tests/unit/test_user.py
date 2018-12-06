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

from django import test
import mock

from openstack_auth import user


class PermTestCase(test.TestCase):
    def test_has_perms(self):
        testuser = user.User(id=1, roles=[])

        def has_perm(perm, obj=None):
            return perm in ('perm1', 'perm3')

        with mock.patch.object(testuser, 'has_perm', side_effect=has_perm):
            self.assertFalse(testuser.has_perms(['perm2']))

            # perm1 AND perm3
            self.assertFalse(testuser.has_perms(['perm1', 'perm2']))

            # perm1 AND perm3
            self.assertTrue(testuser.has_perms(['perm1', 'perm3']))

            # perm1 AND (perm2 OR perm3)
            perm_list = ['perm1', ('perm2', 'perm3')]
            self.assertTrue(testuser.has_perms(perm_list))
