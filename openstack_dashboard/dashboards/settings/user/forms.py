# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

import pytz

from django import shortcuts
from django.conf import settings
from django.utils import translation

from horizon import forms
from horizon import messages


class UserSettingsForm(forms.SelfHandlingForm):
    language = forms.ChoiceField()
    timezone = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(UserSettingsForm, self).__init__(*args, **kwargs)

        # Languages
        languages = [(k, "%s (%s)"
                      % (translation.get_language_info(k)['name_local'], k))
                      for k, v in settings.LANGUAGES]
        self.fields['language'].choices = languages

        # Timezones
        timezones = [(tz, tz) for tz in pytz.common_timezones]
        self.fields['timezone'].choices = timezones

    def handle(self, request, data):
        response = shortcuts.redirect(request.build_absolute_uri())
        # Language
        lang_code = data['language']
        if lang_code and translation.check_for_language(lang_code):
            if hasattr(request, 'session'):
                request.session['django_language'] = lang_code
            else:
                response.set_cookie(settings.LANGUAGE_COOKIE_NAME, lang_code)

        # Timezone
        request.session['django_timezone'] = pytz.timezone(data['timezone'])

        messages.success(request, translation.ugettext("Settings saved."))

        return response
