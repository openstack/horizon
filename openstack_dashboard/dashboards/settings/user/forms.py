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
import gettext as gettext_module
import itertools
import string

import babel
import babel.dates
from django.conf import settings
from django import shortcuts
from django.utils import encoding
from django.utils import lru_cache
from django.utils import translation
from django.utils.translation import ugettext_lazy as _
import pytz

from horizon import forms
from horizon import messages
from horizon.utils import functions


def _get_language_display_name(code, desc):
    try:
        desc = translation.get_language_info(code)['name_local']
        desc = string.capwords(desc)
    except KeyError:
        # If a language is not defined in django.conf.locale.LANG_INFO
        # get_language_info raises KeyError
        pass
    return "%s (%s)" % (desc, code)


@lru_cache.lru_cache()
def _get_languages():

    languages = []
    processed_catalogs = set([])
    # sorted() here is important to make processed_catalogs checking
    # work properly.
    for lang_code, lang_label in sorted(settings.LANGUAGES):
        if lang_code == 'en':
            # Add English as source language
            languages.append(('en',
                              _get_language_display_name('en', 'English')))
            continue
        found_catalogs = [
            gettext_module.find(domain, locale_path,
                                [translation.to_locale(lang_code)])
            for locale_path, domain
            in itertools.product(settings.LOCALE_PATHS,
                                 ['django', 'djangojs'])
        ]
        if not all(found_catalogs):
            continue
        # NOTE(amotoki):
        # Check if found catalogs are already processed or not.
        # settings.LANGUAGES can contains languages with a same prefix
        # like es, es-ar, es-mx. gettext_module.find() searchess Message
        # catalog for es-ar in the order of 'es_AR' and then 'es'.
        # If 'es' locale is translated, 'es-ar' is included in the list of
        # found_catalogs even if 'es-ar' is not translated.
        # In this case, the list already includes 'es' and
        # there is no need to include 'es-ar'.
        result = [catalog in processed_catalogs
                  for catalog in found_catalogs]
        if any(result):
            continue
        processed_catalogs |= set(found_catalogs)
        languages.append(
            (lang_code,
             _get_language_display_name(lang_code, lang_label))
        )
    return sorted(languages)


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

        self.fields['language'].choices = _get_languages()

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
        if lang_code and translation.check_for_language(lang_code):
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
