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

import datetime

from horizon.test import utils


class DummyBackend(object):
    _user = utils.ObjDictWrapper(
        id="1",
        nam='test_user',
        email='test@example.com',
        password='password',
        token=utils.ObjDictWrapper(
            expires=datetime.datetime.now() + datetime.timedelta(30)),
        project_id='1',
        enabled=True,
        domain_id="1",

        is_active=True,
        pk=1111,
        save=lambda *args, **kwargs: None,
        is_authenticated=lambda: True,
        has_perms=lambda perms: True)

    def authenticate(self, *args, **kwargs):
        return self._user

    def get_user(self, user_id):
        return self._user
