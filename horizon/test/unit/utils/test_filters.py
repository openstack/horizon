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

import datetime

import django.template
from django.template import defaultfilters

from horizon.test import helpers as test
from horizon.utils import filters
# we have to import the filter in order to register it
from horizon.utils.filters import parse_isotime  # noqa: F401


class FiltersTests(test.TestCase):
    def test_replace_underscore_filter(self):
        res = filters.replace_underscores("__under_score__")
        self.assertEqual("  under score  ", res)

    def test_parse_isotime_filter(self):
        c = django.template.Context({'time': ''})
        t = django.template.Template('{{ time|parse_isotime }}')
        output = u""

        self.assertEqual(output, t.render(c))

        c = django.template.Context({'time': 'error'})
        t = django.template.Template('{{ time|parse_isotime }}')
        output = u""

        self.assertEqual(output, t.render(c))

        c = django.template.Context({'time': 'error'})
        t = django.template.Template('{{ time|parse_isotime:"test" }}')
        output = u"test"

        self.assertEqual(output, t.render(c))

        c = django.template.Context({'time': '2007-03-04T21:08:12'})
        t = django.template.Template('{{ time|parse_isotime:"test" }}')
        output = u"March 4, 2007, 9:08 p.m."

        self.assertEqual(output, t.render(c))

        adate = '2007-01-25T12:00:00Z'
        result = filters.parse_isotime(adate)
        self.assertIsInstance(result, datetime.datetime)


class TimeSinceNeverFilterTests(test.TestCase):

    default = u"Never"

    def test_timesince_or_never_returns_default_for_empty_string(self):
        c = django.template.Context({'time': ''})
        t = django.template.Template('{{ time|timesince_or_never }}')
        self.assertEqual(self.default, t.render(c))

    def test_timesince_or_never_returns_default_for_none(self):
        c = django.template.Context({'time': None})
        t = django.template.Template('{{ time|timesince_or_never }}')
        self.assertEqual(self.default, t.render(c))

    def test_timesince_or_never_returns_default_for_gibberish(self):
        c = django.template.Context({'time': django.template.Context()})
        t = django.template.Template('{{ time|timesince_or_never }}')
        self.assertEqual(self.default, t.render(c))

    def test_timesince_or_never_returns_with_custom_default(self):
        custom = "Hello world"
        c = django.template.Context({'date': ''})
        t = django.template.Template('{{ date|timesince_or_never:"%s" }}'
                                     % custom)
        self.assertEqual(custom, t.render(c))

    def test_timesince_or_never_returns_with_custom_empty_string_default(self):
        c = django.template.Context({'date': ''})
        t = django.template.Template('{{ date|timesince_or_never:"" }}')
        self.assertEqual("", t.render(c))

    def test_timesince_or_never_returns_same_output_as_django_date(self):
        d = datetime.date(year=2014, month=3, day=7)
        c = django.template.Context({'date': d})
        t = django.template.Template('{{ date|timesince_or_never }}')
        self.assertEqual(defaultfilters.timesince(d), t.render(c))

    def test_timesince_or_never_returns_same_output_as_django_datetime(self):
        now = datetime.datetime.now()
        c = django.template.Context({'date': now})
        t = django.template.Template('{{ date|timesince_or_never }}')
        self.assertEqual(defaultfilters.timesince(now), t.render(c))
