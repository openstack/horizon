# Copyright 2015 Cisco Systems, Inc.
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


from django.conf import settings
from django.core import urlresolvers
from django.core.urlresolvers import reverse
from django.utils.importlib import import_module  # noqa

from horizon import base

from openstack_dashboard.contrib.developer.dashboard import Developer
from openstack_dashboard.test import helpers as test


class ThemePreviewTests(test.TestCase):

    # Manually register Developer Dashboard, as DEBUG=False in tests
    def setUp(self):
        super(ThemePreviewTests, self).setUp()
        urlresolvers.clear_url_caches()
        reload(import_module(settings.ROOT_URLCONF))
        base.Horizon.register(Developer)
        base.Horizon._urls()

    def tearDown(self):
        super(ThemePreviewTests, self).tearDown()
        base.Horizon.unregister(Developer)
        base.Horizon._urls()

    def test_index(self):
        index = reverse('horizon:developer:theme_preview:index')
        res = self.client.get(index)
        self.assertTemplateUsed(res, 'developer/theme_preview/index.html')
