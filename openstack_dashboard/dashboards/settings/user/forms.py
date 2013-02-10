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

from datetime import datetime
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
        d = datetime(datetime.today().year, 1, 1)
        timezones = []
        for tz in pytz.common_timezones:
            try:
                utc_offset = pytz.timezone(tz).localize(d).strftime('%z')
                utc_offset = " (UTC %s:%s)" % (utc_offset[:3], utc_offset[3:])
            except:
                utc_offset = ""

            if tz != "UTC":
                tz_name = "%s%s" % (tz, utc_offset)
            else:
                tz_name = tz
            timezones.append((tz, tz_name))

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
        request.session['django_timezone'] = pytz.timezone(
            data['timezone']).zone

        messages.success(request, translation.ugettext("Settings saved."))

        return response
