# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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

import datetime
import logging
import re

from django import utils
from django.conf import settings
from django.contrib import messages
from django.forms import widgets
from django.utils import dates
from django.utils import safestring
from django.utils import formats

from django.forms import *

LOG = logging.getLogger('django_openstack.forms')
RE_DATE = re.compile(r'(\d{4})-(\d\d?)-(\d\d?)$')


class SelectDateWidget(widgets.Widget):
    """
    A Widget that splits date input into three <select> boxes.

    This also serves as an example of a Widget that has more than one HTML
    element and hence implements value_from_datadict.
    """
    none_value = (0, '---')
    month_field = '%s_month'
    day_field = '%s_day'
    year_field = '%s_year'

    def __init__(self, attrs=None, years=None, required=True,
            skip_day_field=False):
        # years is an optional list/tuple of years to use in
        # the "year" select box.
        self.attrs = attrs or {}
        self.required = required
        self.skip_day_field = skip_day_field
        if years:
            self.years = years
        else:
            this_year = datetime.date.today().year
            self.years = range(this_year, this_year + 10)

    def render(self, name, value, attrs=None, skip_day_field=True):
        try:
            year_val, month_val, day_val = value.year, value.month, value.day
        except AttributeError:
            year_val = month_val = day_val = None
            if isinstance(value, basestring):
                if settings.USE_L10N:
                    try:
                        input_format = formats.get_format(
                                'DATE_INPUT_FORMATS')[0]
                        # Python 2.4 compatibility:
                        #     v = datetime.datetime.strptime(value,
                        #                                    input_format)
                        # would be clearer, but datetime.strptime was added in
                        # Python 2.5
                        v = datetime.datetime(*(time.strptime(value,
                            input_format)[0:6]))
                        year_val, month_val, day_val = v.year, v.month, v.day
                    except ValueError:
                        pass
                else:
                    match = RE_DATE.match(value)
                    if match:
                        year_val, month_val, day_val = \
                                [int(v) for v in match.groups()]
        choices = [(i, i) for i in self.years]
        year_html = self.create_select(name,
                self.year_field, value, year_val, choices)
        choices = dates.MONTHS.items()
        month_html = self.create_select(name,
                self.month_field, value, month_val, choices)
        choices = [(i, i) for i in range(1, 32)]
        day_html = self.create_select(name,
                self.day_field, value, day_val,  choices)

        format = formats.get_format('DATE_FORMAT')
        escaped = False
        output = []
        for char in format:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char in 'Yy':
                output.append(year_html)
            elif char in 'bFMmNn':
                output.append(month_html)
            elif char in 'dj' and not self.skip_day_field:
                output.append(day_html)
        return safestring.mark_safe(u'\n'.join(output))

    def id_for_label(self, id_):
        return '%s_month' % id_
    id_for_label = classmethod(id_for_label)

    def value_from_datadict(self, data, files, name):
        y = data.get(self.year_field % name)
        m = data.get(self.month_field % name)
        d = data.get(self.day_field % name)
        if y == m == d == "0":
            return None
        if y and m and d:
            if settings.USE_L10N:
                input_format = formats.get_format('DATE_INPUT_FORMATS')[0]
                try:
                    date_value = datetime.date(int(y), int(m), int(d))
                except ValueError:
                    pass
                else:
                    date_value = utils.datetime_safe.new_date(date_value)
                    return date_value.strftime(input_format)
            else:
                return '%s-%s-%s' % (y, m, d)
        return data.get(name, None)

    def create_select(self, name, field, value, val, choices):
        if 'id' in self.attrs:
            id_ = self.attrs['id']
        else:
            id_ = 'id_%s' % name
        if not (self.required and val):
            choices.insert(0, self.none_value)
        local_attrs = self.build_attrs(id=field % id_)
        s = widgets.Select(choices=choices)
        select_html = s.render(field % name, val, local_attrs)
        return select_html


class SelfHandlingForm(Form):
    method = CharField(required=True, widget=HiddenInput)

    def __init__(self, *args, **kwargs):
        initial = kwargs.pop('initial', {})
        initial['method'] = self.__class__.__name__
        kwargs['initial'] = initial
        super(SelfHandlingForm, self).__init__(*args, **kwargs)

    @classmethod
    def maybe_handle(cls, request, *args, **kwargs):
        if cls.__name__ != request.POST.get('method'):
            return cls(*args, **kwargs), None

        try:
            if request.FILES:
                form = cls(request.POST, request.FILES, *args, **kwargs)
            else:
                form = cls(request.POST, *args, **kwargs)

            if not form.is_valid():
                return form, None

            data = form.clean()

            return form, form.handle(request, data)
        except Exception as e:
            LOG.exception('Nonspecific error while handling form')
            messages.error(request, _('Unexpected error: %s') % e.message)
            return form, None


class DateForm(Form):
    date = DateField(widget=SelectDateWidget(
        years=range(datetime.date.today().year, 2009, -1),
        skip_day_field=True))
