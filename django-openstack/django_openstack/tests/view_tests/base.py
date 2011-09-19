# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula Inc.
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
Base classes for view based unit tests.
"""
from django import http
from django import shortcuts
from django import test as django_test
from django import template as django_template
from django.conf import settings
from django_openstack import test


def fake_render_to_response(template_name, context, context_instance=None,
                            mimetype='text/html'):
    """Replacement for render_to_response so that views can be tested
       without having to stub out templates that belong in the frontend
       implementation.

       Should be able to be tested using the django unit test assertions like a
       normal render_to_response return value can be.
    """
    class Template(object):
        def __init__(self, name):
            self.name = name

    if context_instance is None:
        context_instance = django_template.Context(context)
    else:
        context_instance.update(context)

    resp = http.HttpResponse()
    template = Template(template_name)

    resp.write('<html><body><p>'
               'This is a fake httpresponse for testing purposes only'
               '</p></body></html>')

    # Allows django.test.client to populate fields on the response object
    django_test.signals.template_rendered.send(template, template=template,
                                               context=context_instance)

    return resp


class BaseViewTests(test.TestCase):
    def setUp(self):
        super(BaseViewTests, self).setUp()
        self._real_render_to_response = shortcuts.render_to_response
        shortcuts.render_to_response = fake_render_to_response

    def tearDown(self):
        super(BaseViewTests, self).tearDown()
        shortcuts.render_to_response = self._real_render_to_response

    def assertRedirectsNoFollow(self, response, expected_url):
        self.assertEqual(response._headers['location'],
                         ('Location', settings.TESTSERVER + expected_url))
        self.assertEqual(response.status_code, 302)
