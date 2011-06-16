# vim: tabstop=4 shiftwidth=4 softtabstop=4

import logging

from django.contrib import messages
from django.forms import *

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
            form = cls(request.POST, *args, **kwargs)

            if not form.is_valid():
                return form, None

            data = form.clean()

            return form, form.handle(request, data)
        except Exception as e:
            logging.exception('Error while handling form.')
            messages.error(request, 'Unexpected error: %s' % e.message)
            return form, None
