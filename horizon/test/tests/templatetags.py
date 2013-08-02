# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
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

import re

from django.conf import settings  # noqa
from django.template import Context  # noqa
from django.template import Template  # noqa
from django.utils.text import normalize_newlines  # noqa

from horizon.test import helpers as test


def single_line(text):
    ''' Quick utility to make comparing template output easier. '''
    return re.sub(' +',
                  ' ',
                  normalize_newlines(text).replace('\n', '')).strip()


class TemplateTagTests(test.TestCase):
    '''Test Custom Template Tag'''
    def render_template_tag(self, tag_name, tag_require=''):
        '''Render a Custom Template Tag to string'''
        template = Template("{%% load %s %%}{%% %s %%}"
                            % (tag_require, tag_name))
        return template.render(Context())

    def test_site_branding_tag(self):
        '''Test if site_branding tag renders the correct setting'''
        rendered_str = self.render_template_tag("site_branding", "branding")
        self.assertEqual(settings.SITE_BRANDING, rendered_str.strip(),
                        "tag site_branding renders %s" % rendered_str.strip())
