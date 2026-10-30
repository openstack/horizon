# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import io

from horizon.test import helpers as test
from horizon.utils.babel_extract_django import extract_django

default_keys = []


class ExtractDjangoTestCase(test.TestCase):

    def test_blocktrans(self):
        template_content = """
                {% load i18n %}
                <h1>{% trans "Hello World" %}</h1>

                {% blocktrans %}Welcome, {{ name }}!{% endblocktrans %}
                """
        fileobj = io.BytesIO(template_content.encode('utf-8'))

        messages = list(extract_django(fileobj, [], [], {'encoding': 'utf-8'}))

        self.assertEqual(messages[0][2], "Hello World")
        self.assertEqual(messages[1][2], "Welcome, %(name)s!")

    def test_gettext_lazy(self):
        template_content = '{{ _("Click here to continue") }}'
        fileobj = io.BytesIO(template_content.encode('utf-8'))

        messages = list(extract_django(fileobj, [], [], {}))
        self.assertEqual(messages[0][2], "Click here to continue")

    def test_extract_with_context(self):
        template_content = '{% trans "May" context "month name" %}'
        fileobj = io.BytesIO(template_content.encode('utf-8'))

        messages = list(extract_django(fileobj, [], [], {}))

        # For context-based translations Django returns ['context', 'message']
        self.assertEqual(messages[0][1], 'pgettext')
        self.assertEqual(messages[0][2][0], "month name")
        self.assertEqual(messages[0][2][1], "May")
