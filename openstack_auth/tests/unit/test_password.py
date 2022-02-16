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

from unittest import mock

from django import test

from openstack_auth import forms
from openstack_auth.tests.unit.test_auth import IsA


class ChangePasswordTests(test.TestCase):
    @test.override_settings(
        ALLOW_USERS_CHANGE_EXPIRED_PASSWORD=True,
        AVAILABLE_REGIONS=[
            ("x", 'region1'),
            ("y", 'region2'),
        ],  # we need at least two regions for the choice field to be visible
    )
    def test_change_password(self):
        form_data = {
            'region': '0',
            'original_password': 'oldpwd',
            'password': 'normalpwd',
            'confirm_password': 'normalpwd',
        }
        initial = {
            'user_id': 'user',
            'region': '0',
        }

        form = forms.Password(form_data, initial=initial)
        client = mock.Mock()

        with mock.patch(
            'openstack_auth.utils.get_session',
            return_value=mock.sentinel.session
        ) as mock_get_session:
            with mock.patch(
                'openstack_auth.utils.get_keystone_client',
                return_value=client
            ) as mock_get_keystone_client:
                form.is_valid()

        self.assertFalse(form.errors)
        mock_get_session.assert_called_once_with(auth=IsA(forms.DummyAuth))
        mock_get_keystone_client.assert_called_once_with()
        client.Client.assert_called_once_with(
            session=mock.sentinel.session,
            user_id='user',
            auth_url='x',
            endpoint='x',
        )

    @test.override_settings(
        AVAILABLE_REGIONS=[
            ("x", 'region1'),
            ("y", 'region2'),
        ],
    )
    def test_change_password_with_error(self):
        form_data = {
            'region': '0',
            'original_password': 'oldpwd',
            'password': 'normalpwd',
            'confirm_password': 'normalpwd1',
        }
        initial = {
            'user_id': 'user',
            'region': '0',
        }

        form = forms.Password(form_data, initial=initial)

        self.assertTrue(form.errors)
        self.assertIn(['Passwords do not match.'], form.errors.values())
