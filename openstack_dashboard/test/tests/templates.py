# Copyright (c) 2012 OpenStack Foundation
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

from django import template
from django.template import loader

from openstack_dashboard.test import helpers as test


class FakeUser(object):
    username = "cool user"


class TemplateRenderTest(test.TestCase):
    """Tests for templates render."""

    def test_openrc_html_escape(self):
        context = {
            "user": FakeUser(),
            "tenant_id": "some-cool-id",
            "auth_url": "http://tests.com",
            "tenant_name": "ENG Perf R&D"}
        out = loader.render_to_string(
            'project/access_and_security/api_access/openrc.sh.template',
            context,
            template.Context(context))

        self.assertFalse("&amp;" in out)
        self.assertTrue("ENG Perf R&D" in out)

    def test_openrc_html_evil_shell_escape(self):
        context = {
            "user": FakeUser(),
            "tenant_id": "some-cool-id",
            "auth_url": "http://tests.com",
            "tenant_name": 'o"; sudo rm -rf /'}
        out = loader.render_to_string(
            'project/access_and_security/api_access/openrc.sh.template',
            context,
            template.Context(context))

        self.assertFalse('o"' in out)
        self.assertTrue('\"' in out)

    def test_openrc_html_evil_shell_backslash_escape(self):
        context = {
            "user": FakeUser(),
            "tenant_id": "some-cool-id",
            "auth_url": "http://tests.com",
            "tenant_name": 'o\"; sudo rm -rf /'}
        out = loader.render_to_string(
            'project/access_and_security/api_access/openrc.sh.template',
            context,
            template.Context(context))

        self.assertFalse('o\"' in out)
        self.assertFalse('o"' in out)
        self.assertTrue('\\"' in out)

    def test_openrc_set_region(self):
        context = {
            "user": FakeUser(),
            "tenant_id": "some-cool-id",
            "auth_url": "http://tests.com",
            "tenant_name": "Tenant",
            "region": "Colorado"}
        out = loader.render_to_string(
            'project/access_and_security/api_access/openrc.sh.template',
            context,
            template.Context(context))

        self.assertTrue("OS_REGION_NAME=\"Colorado\"" in out)

    def test_openrc_region_not_set(self):
        context = {
            "user": FakeUser(),
            "tenant_id": "some-cool-id",
            "auth_url": "http://tests.com",
            "tenant_name": "Tenant"}
        out = loader.render_to_string(
            'project/access_and_security/api_access/openrc.sh.template',
            context,
            template.Context(context))

        self.assertTrue("OS_REGION_NAME=\"\"" in out)
