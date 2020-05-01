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
import string

import babel
import babel.dates
from django.conf import settings
from django import shortcuts
from django.utils import encoding
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
import pytz

from horizon import forms
from horizon import messages
from horizon.utils import functions


class UserSettingsForm(forms.SelfHandlingForm):
    max_value = getattr(settings, 'API_RESULT_LIMIT', 1000)
    language = forms.ChoiceField(label=_("Language"))
    timezone = forms.ChoiceField(label=_("Timezone"))
    pagesize = forms.IntegerField(label=_("Items Per Page"),
                                  min_value=1,
                                  max_value=max_value)
    instance_log_length = forms.IntegerField(
        label=_("Log Lines Per Instance"), min_value=1,
        help_text=_("Number of log lines to be shown per instance"))

    @staticmethod
    def _sorted_zones():
        d = datetime(datetime.today().year, 1, 1)
        zones = [(tz, pytz.timezone(tz).localize(d).strftime('%z'))
                 for tz in pytz.common_timezones]
        zones.sort(key=lambda zone: int(zone[1]))
        return zones

    def __init__(self, *args, **kwargs):
        super(UserSettingsForm, self).__init__(*args, **kwargs)

        # Languages
        def get_language_display_name(code, desc):
            try:
                desc = translation.get_language_info(code)['name_local']
                desc = string.capwords(desc)
            except KeyError:
                # If a language is not defined in django.conf.locale.LANG_INFO
                # get_language_info raises KeyError
                pass
            return "%s (%s)" % (desc, code)
        languages = [(k, get_language_display_name(k, v))
                     for k, v in settings.LANGUAGES]
        self.fields['language'].choices = languages

        # Timezones
        timezones = []
        language = translation.get_language()
        current_locale = translation.to_locale(language)
        babel_locale = babel.Locale.parse(current_locale)
        for tz, offset in self._sorted_zones():
            try:
                utc_offset = _("UTC %(hour)s:%(min)s") % {"hour": offset[:3],
                                                          "min": offset[3:]}
            except Exception:
                utc_offset = ""

            if tz == "UTC":
                tz_name = _("UTC")
            elif tz == "GMT":
                tz_name = _("GMT")
            else:
                tz_label = babel.dates.get_timezone_location(
                    tz, locale=babel_locale)
                # Translators:  UTC offset and timezone label
                tz_name = _("%(offset)s: %(label)s") % {"offset": utc_offset,
                                                        "label": tz_label}
            timezones.append((tz, tz_name))

        self.fields['timezone'].choices = timezones

        # When we define a help_text using any variable together with
        # form field, traslation does not work well.
        # To avoid this, we define here. (#1563021)
        self.fields['pagesize'].help_text = (
            _("Number of items to show per page (applies to the pages "
              "that have API supported pagination, Max Value: %s)")
            % self.max_value)

    def handle(self, request, data):
        response = shortcuts.redirect(request.build_absolute_uri())

        lang_code = data['language']
        response = functions.save_config_value(
            request, response, settings.LANGUAGE_COOKIE_NAME, lang_code)

        response = functions.save_config_value(
            request, response, 'django_timezone',
            pytz.timezone(data['timezone']).zone)

        response = functions.save_config_value(
            request, response, 'API_RESULT_PAGE_SIZE', data['pagesize'])

        response = functions.save_config_value(
            request, response, 'INSTANCE_LOG_LENGTH',
            data['instance_log_length'])

        with translation.override(lang_code):
            messages.success(request,
                             encoding.force_text(_("Settings saved.")))

        return response
