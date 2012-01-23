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

from datetime import date
import logging

from django import forms
from django.utils import dates

from horizon import exceptions


LOG = logging.getLogger(__name__)


class SelfHandlingForm(forms.Form):
    """
    A base :class:`Form <django:django.forms.Form>` class which includes
    processing logic in its subclasses and handling errors raised during
    form processing.

    .. attribute:: method

        A :class:`CharField <django:django.forms.CharField>` instance
        rendered with a
        :class:`CharField <django:django.forms.widgets.HiddenInput>`
        widget which is automatically set to the value of the class name.

        This is used to determine whether this form should handle the
        input it is given or not.
    """
    method = forms.CharField(required=True, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        initial = kwargs.pop('initial', {})
        initial['method'] = self.__class__.__name__
        kwargs['initial'] = initial
        super(SelfHandlingForm, self).__init__(*args, **kwargs)

    @classmethod
    def _instantiate(cls, request, *args, **kwargs):
        """ Instantiates the form. Allows customization in subclasses. """
        return cls(*args, **kwargs)

    @classmethod
    def maybe_handle(cls, request, *args, **kwargs):
        """
        If the form is valid,
        :meth:`~horizon.forms.SelfHandlingForm.maybe_handle` calls a
        ``handle(request, data)`` method on its subclass to
        determine what action to take.

        Any exceptions raised during processing are captured and
        converted to messages.
        """

        if request.method != 'POST' or \
                cls.__name__ != request.POST.get('method'):
            return cls._instantiate(request, *args, **kwargs), None

        if request.FILES:
            form = cls._instantiate(request, request.POST, request.FILES,
                                    *args, **kwargs)
        else:
            form = cls._instantiate(request, request.POST, *args, **kwargs)

        if not form.is_valid():
            return form, None

        data = form.clean()

        try:
            return form, form.handle(request, data)
        except:
            exceptions.handle(request)
            return form, None


class DateForm(forms.Form):
    """ A simple form for selecting a start date. """
    month = forms.ChoiceField(choices=dates.MONTHS.items())
    year = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(DateForm, self).__init__(*args, **kwargs)
        years = [(year, year) for year in xrange(2009, date.today().year + 1)]
        years.reverse()
        self.fields['year'].choices = years
