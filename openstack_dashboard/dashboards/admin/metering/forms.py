# Copyright 2014 OpenStack Foundation
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

from django.forms import ValidationError  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import forms


class UsageReportForm(forms.SelfHandlingForm):
    PERIOD_CHOICES = (("1", _("Last day")),
                      ("7", _("Last week")),
                      (str(datetime.date.today().day), _("Month to date")),
                      ("15", _("Last 15 days")),
                      ("30", _("Last 30 days")),
                      ("365", _("Last year")),
                      ("other", _("Other")),
                      )
    period = forms.ChoiceField(label=_("Period"),
                               required=True,
                               choices=PERIOD_CHOICES)
    date_from = forms.DateField(label=_("From"), required=False,
                                widget=forms.TextInput(
                                attrs={'data-date-picker': True}))
    date_to = forms.DateField(label=_("To"), required=False,
                              widget=forms.TextInput(
                              attrs={'data-date-picker': True}))

    def clean_date_from(self):
        period = self.cleaned_data['period']
        date_from = self.cleaned_data['date_from']
        if period == 'other' and date_from is None:
            raise ValidationError(_('Must specify start of period'))
        return date_from

    def clean_date_to(self):
        data = super(UsageReportForm, self).clean()
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        period = data.get('period')
        if (period == 'other' and date_to is not None
                and date_from is not None and date_to < date_from):
            raise ValidationError(_("Start must be earlier "
                                    "than end of period."))
        else:
            return date_to

    def handle(self, request, data):
        if hasattr(request, 'session'):
            request.session['date_from'] = data['date_from']
            request.session['date_to'] = data['date_to']
            request.session['period'] = data['period']
        return data
