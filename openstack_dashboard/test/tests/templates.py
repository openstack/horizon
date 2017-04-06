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

import yaml

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
            'project/api_access/openrc.sh.template',
            context,
            template.Context(context))

        self.assertNotIn("&amp;", out)
        self.assertIn("ENG Perf R&D", out)

    def test_openrc_html_evil_shell_escape(self):
        context = {
            "user": FakeUser(),
            "tenant_id": "some-cool-id",
            "auth_url": "http://tests.com",
            "tenant_name": 'o"; sudo rm -rf /'}
        out = loader.render_to_string(
            'project/api_access/openrc.sh.template',
            context,
            template.Context(context))

        self.assertNotIn('o"', out)
        self.assertIn('\"', out)

    def test_openrc_html_evil_shell_backslash_escape(self):
        context = {
            "user": FakeUser(),
            "tenant_id": "some-cool-id",
            "auth_url": "http://tests.com",
            "tenant_name": 'o\"; sudo rm -rf /'}
        out = loader.render_to_string(
            'project/api_access/openrc.sh.template',
            context,
            template.Context(context))

        self.assertNotIn('o\"', out)
        self.assertNotIn('o"', out)
        self.assertIn('\\"', out)

    def test_openrc_set_region(self):
        context = {
            "user": FakeUser(),
            "tenant_id": "some-cool-id",
            "auth_url": "http://tests.com",
            "tenant_name": "Tenant",
            "region": "Colorado"}
        out = loader.render_to_string(
            'project/api_access/openrc.sh.template',
            context,
            template.Context(context))

        self.assertIn("OS_REGION_NAME=\"Colorado\"", out)

    def test_openrc_region_not_set(self):
        context = {
            "user": FakeUser(),
            "tenant_id": "some-cool-id",
            "auth_url": "http://tests.com",
            "tenant_name": "Tenant"}
        out = loader.render_to_string(
            'project/api_access/openrc.sh.template',
            context,
            template.Context(context))

        self.assertIn("OS_REGION_NAME=\"\"", out)

    def test_clouds_yaml_set_region(self):
        context = {
            "cloud_name": "openstack",
            "user": FakeUser(),
            "tenant_id": "some-cool-id",
            "auth_url": "http://example.com",
            "tenant_name": "Tenant",
            "region": "Colorado"}
        out = yaml.load(loader.render_to_string(
            'project/api_access/clouds.yaml.template',
            context,
            template.Context(context)))

        self.assertIn('clouds', out)
        self.assertIn('openstack', out['clouds'])
        self.assertNotIn('profile', out['clouds']['openstack'])
        self.assertEqual(
            "http://example.com",
            out['clouds']['openstack']['auth']['auth_url'])
        self.assertEqual("Colorado", out['clouds']['openstack']['region_name'])
        self.assertNotIn('regions', out['clouds']['openstack'])

    def test_clouds_yaml_region_not_set(self):
        context = {
            "cloud_name": "openstack",
            "user": FakeUser(),
            "tenant_id": "some-cool-id",
            "auth_url": "http://example.com",
            "tenant_name": "Tenant"}
        out = yaml.load(loader.render_to_string(
            'project/api_access/clouds.yaml.template',
            context,
            template.Context(context)))

        self.assertIn('clouds', out)
        self.assertIn('openstack', out['clouds'])
        self.assertNotIn('profile', out['clouds']['openstack'])
        self.assertEqual(
            "http://example.com",
            out['clouds']['openstack']['auth']['auth_url'])
        self.assertNotIn('region_name', out['clouds']['openstack'])
        self.assertNotIn('regions', out['clouds']['openstack'])

    def test_clouds_yaml_regions(self):
        regions = ['region1', 'region2']
        context = {
            "cloud_name": "openstack",
            "user": FakeUser(),
            "tenant_id": "some-cool-id",
            "auth_url": "http://example.com",
            "tenant_name": "Tenant",
            "regions": regions}
        out = yaml.load(loader.render_to_string(
            'project/api_access/clouds.yaml.template',
            context,
            template.Context(context)))

        self.assertIn('clouds', out)
        self.assertIn('openstack', out['clouds'])
        self.assertNotIn('profile', out['clouds']['openstack'])
        self.assertEqual(
            "http://example.com",
            out['clouds']['openstack']['auth']['auth_url'])
        self.assertNotIn('region_name', out['clouds']['openstack'])
        self.assertIn('regions', out['clouds']['openstack'])
        self.assertEqual(regions, out['clouds']['openstack']['regions'])

    def test_clouds_yaml_profile(self):
        regions = ['region1', 'region2']
        context = {
            "cloud_name": "openstack",
            "user": FakeUser(),
            "profile": "example",
            "tenant_id": "some-cool-id",
            "auth_url": "http://example.com",
            "tenant_name": "Tenant",
            "regions": regions}
        out = yaml.load(loader.render_to_string(
            'project/api_access/clouds.yaml.template',
            context,
            template.Context(context)))

        self.assertIn('clouds', out)
        self.assertIn('openstack', out['clouds'])
        self.assertIn('profile', out['clouds']['openstack'])
        self.assertEqual('example', out['clouds']['openstack']['profile'])
        self.assertNotIn('auth_url', out['clouds']['openstack']['auth'])
        self.assertNotIn('region_name', out['clouds']['openstack'])
        self.assertNotIn('regions', out['clouds']['openstack'])
