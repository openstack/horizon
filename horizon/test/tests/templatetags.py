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

from django.conf import settings
from django.template import Context  # noqa
from django.template import Template  # noqa
from django.utils.text import normalize_newlines  # noqa

from horizon.test import helpers as test


def single_line(text):
    """Quick utility to make comparing template output easier."""
    return re.sub(' +',
                  ' ',
                  normalize_newlines(text).replace('\n', '')).strip()


class TemplateTagTests(test.TestCase):
    """Test Custom Template Tag."""
    def render_template_tag(self, tag_name, tag_require=''):
        tag_call = "{%% %s %%}" % tag_name
        return self.render_template(tag_call, tag_require)

    def render_template(self, template_text, tag_require='', context={}):
        """Render a Custom Template to string."""
        template = Template("{%% load %s %%} %s"
                            % (tag_require, template_text))
        return template.render(Context(context))

    def test_site_branding_tag(self):
        """Test if site_branding tag renders the correct setting."""
        rendered_str = self.render_template_tag("site_branding", "branding")
        self.assertEqual(settings.SITE_BRANDING, rendered_str.strip(),
                        "tag site_branding renders %s" % rendered_str.strip())

    def test_size_format_filters(self):
        size_str = ('5|diskgbformat', '10|diskgbformat',
                    '5555|mb_float_format', '80|mb_float_format',
                    '.5|mbformat', '0.005|mbformat', '0.0005|mbformat')
        expected = u' 5.0GB 10.0GB 5.4GB 80.0MB 512KB 5KB 524Bytes '

        text = ''
        for size_filter in size_str:
            text += '{{' + size_filter + '}} '

        rendered_str = self.render_template(tag_require='sizeformat',
                                            template_text=text)
        self.assertEqual(rendered_str, expected)

    def test_size_format_filters_with_string(self):
        size_str = ('"test"|diskgbformat', '"limit"|mb_float_format',
                    '"no limit"|mbformat')
        expected = u' test limit no limit '

        text = ''
        for size_filter in size_str:
            text += '{{' + size_filter + '}} '

        rendered_str = self.render_template(tag_require='sizeformat',
                                            template_text=text)
        self.assertEqual(rendered_str, expected)

    def test_truncate_filter(self):
        ctx_string = {'val1': 'he',
                      'val2': 'hellotrunc',
                      'val3': 'four'}

        text = ('{{test.val1|truncate:1}}#{{test.val2|truncate:4}}#'
                '{{test.val3|truncate:10}}')

        expected = u' h#h...#four'
        rendered_str = self.render_template(tag_require='truncate_filter',
                                            template_text=text,
                                            context={'test': ctx_string})
        self.assertEqual(rendered_str, expected)

    def test_quota_filter(self):
        ctx_string = {'val1': 100,
                      'val2': 1000,
                      'val3': float('inf')}

        text = ('{{test.val1|quota:"TB"}}#{{test.val2|quota}}#'
                '{{test.val3|quota}}')

        expected = u' 100 TB Available#1000 Available#No Limit'

        rendered_str = self.render_template(tag_require='horizon',
                                            template_text=text,
                                            context={'test': ctx_string})
        self.assertEqual(rendered_str, expected)
