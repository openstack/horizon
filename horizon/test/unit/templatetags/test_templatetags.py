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
from django.template import Context
from django.template import Template
from django.utils.text import normalize_newlines

from horizon.test import helpers as test
# The following imports are required to register the dashboards.
from horizon.test.test_dashboards.cats.dashboard import Cats  # noqa: F401
from horizon.test.test_dashboards.cats.kittens.panel import Kittens  # noqa: F401
from horizon.test.test_dashboards.dogs.dashboard import Dogs  # noqa: F401
from horizon.test.test_dashboards.dogs.puppies.panel import Puppies  # noqa: F401


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

    def render_template(self, template_text, tag_require='', context=None):
        """Render a Custom Template to string."""
        context = context or {}
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
        expected = u' 5GB 10GB 5.4GB 80MB 512KB 5KB 524Bytes '

        text = ''
        for size_filter in size_str:
            text += '{{' + size_filter + '}} '

        rendered_str = self.render_template(tag_require='sizeformat',
                                            template_text=text)
        self.assertEqual(expected, rendered_str)

    def test_size_format_filters_with_string(self):
        size_str = ('"test"|diskgbformat', '"limit"|mb_float_format',
                    '"no limit"|mbformat')
        expected = u' test limit no limit '

        text = ''
        for size_filter in size_str:
            text += '{{' + size_filter + '}} '

        rendered_str = self.render_template(tag_require='sizeformat',
                                            template_text=text)
        self.assertEqual(expected, rendered_str)

    def test_truncate_filter(self):
        ctx_string = {'val1': 'he',
                      'val2': 'hellotrunc',
                      'val3': 'four'}

        text = ('{{ test.val1|truncate:1 }}#{{ test.val2|truncate:4 }}#'
                '{{ test.val3|truncate:10 }}')

        expected = u' h#h...#four'
        rendered_str = self.render_template(tag_require='truncate_filter',
                                            template_text=text,
                                            context={'test': ctx_string})
        self.assertEqual(expected, rendered_str)

    def test_quota_filter(self):
        ctx_string = {'val1': 100,
                      'val2': 1000,
                      'val3': float('inf')}

        text = ('{{ test.val1|quota:"TB" }}#{{ test.val2|quota }}#'
                '{{ test.val3|quota }}')

        expected = u' 100 TB Available#1000 Available#(No Limit)'

        rendered_str = self.render_template(tag_require='horizon',
                                            template_text=text,
                                            context={'test': ctx_string})
        self.assertEqual(expected, rendered_str)

    def test_angular_escapes_filter(self):
        ctx_string = {'val1': "\'a \"quotes\" test\'",
                      'val2': "how about line\r\nbreaks",
                      'val3': "\\s\\l\\a\\s\\h"}

        text = ('{% autoescape off %}'
                '<"{{ test.val1|angular_escapes }}",'
                ' "{{ test.val2|angular_escapes }}",'
                ' "{{ test.val3|angular_escapes }}">'
                '{% endautoescape %}')

        expected = (r""" <"\'a \"quotes\" test\'","""
                    r""" "how about line\r\nbreaks","""
                    r""" "\\s\\l\\a\\s\\h">""")

        rendered_str = self.render_template(tag_require='angular',
                                            template_text=text,
                                            context={'test': ctx_string})
        self.assertEqual(expected, rendered_str)

    def test_horizon_main_nav(self):
        text = "{% horizon_main_nav %}"
        expected = """
                <div>
                    <ul class=\"nav nav-tabs\" role=\"tablist\">
                        <li>
                            <a href=\"/cats/\" tabindex='1'>Cats</a>
                        </li>
                        <li>
                            <a href=\"/dogs/\" tabindex='1'>Dogs</a>
                        </li>
                    </ul></div>"""

        rendered_str = self.render_template(tag_require='horizon',
                                            template_text=text,
                                            context={'request': self.request})
        self.assertEqual(single_line(rendered_str), single_line(expected))
