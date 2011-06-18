# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

"""
Unit tests for region views.
"""

from django.core.urlresolvers import reverse
from django_openstack.nova.tests.base import BaseViewTests


TEST_REGION = 'one'


class RegionViewTests(BaseViewTests):
    def test_change(self):
        self.authenticateTestUser()
        session = self.client.session
        session['region'] = 'two'
        session.save()

        data = {'redirect_url': '/',
                'region': TEST_REGION}
        res = self.client.post(reverse('region_change'), data)
        self.assertEqual(self.client.session['region'], TEST_REGION)
        self.assertRedirectsNoFollow(res, '/')
