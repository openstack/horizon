# Copyright 2013 Red Hat, Inc.
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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from django.utils import translation

import mock

from openstack_dashboard.dashboards.settings.user import forms
from openstack_dashboard.test import helpers as test


INDEX_URL = reverse("horizon:settings:user:index")


class UserSettingsTest(test.TestCase):

    def test_timezone_offset_is_displayed(self):
        res = self.client.get(INDEX_URL)

        self.assertContains(res, "UTC +11:00: Australia (Melbourne) Time")
        self.assertContains(res, "UTC -03:00: Falkland Islands Time")
        self.assertContains(res, "UTC -10:00: United States (Honolulu) Time")

    @override_settings(LOCALE_PATHS=['openstack_dashboard/locale'])
    def test_display_language(self):
        # Add an unknown language to LANGUAGES list
        # to check it works with unknown language in the list.
        settings.LANGUAGES += (('unknown', 'Unknown Language'),)

        res = self.client.get(INDEX_URL)
        # In this test, we just checks language list is properly
        # generated without an error as the result depends on
        # existence of translation message catalogs.
        self.assertContains(res, 'English')


class LanguageTest(test.TestCase):
    """Tests for _get_languages()."""

    def setUp(self):
        super(LanguageTest, self).setUp()
        # _get_languages is decorated by lru_cache,
        # so we need to clear cache info before each test run.
        forms._get_languages.cache_clear()

    @staticmethod
    def _patch_gettext_find_all_translated(*args, **kwargs):
        domain = args[0]
        locale_path = args[1]
        locale = args[2][0]
        return '%s/%s/LC_MESSAGES/%s.mo' % (locale_path, locale, domain)

    @override_settings(LANGUAGES=(('de', 'Germany'),
                                  ('en', 'English'),
                                  ('ja', 'Japanese')),
                       LOCALE_PATHS=['horizon/locale',
                                     'openstack_dashboard/locale'])
    def test_language_list_all_translated(self):
        with mock.patch.object(
                forms.gettext_module, 'find',
                side_effect=LanguageTest._patch_gettext_find_all_translated):
            languages = forms._get_languages()
        self.assertEqual(['de', 'en', 'ja'],
                         [code for code, name in languages])

    @override_settings(LANGUAGES=(('de', 'Germany'),
                                  ('en', 'English'),
                                  ('fr', 'French'),
                                  ('ja', 'Japanese')),
                       LOCALE_PATHS=['horizon/locale',
                                     'openstack_dashboard/locale'])
    def test_language_list_partially_translated(self):
        def _patch_gettext_find(*args, **kwargs):
            domain = args[0]
            locale_path = args[1]
            locale = args[2][0]
            # Assume de and fr are partially translated.
            if locale == translation.to_locale('de'):
                if (domain == 'django' and
                        locale_path == 'openstack_dashboard/locale'):
                    return
            elif locale == translation.to_locale('fr'):
                if (domain == 'djangojs' and locale_path == 'horizon/locale'):
                    return
            return '%s/%s/LC_MESSAGES/%s.mo' % (locale_path, locale,
                                                domain)
        with mock.patch.object(
                forms.gettext_module, 'find',
                side_effect=_patch_gettext_find):
            languages = forms._get_languages()
        self.assertEqual(['en', 'ja'],
                         [code for code, name in languages])

    @override_settings(LANGUAGES=(('de', 'Germany'),
                                  ('ja', 'Japanese')),
                       LOCALE_PATHS=['horizon/locale',
                                     'openstack_dashboard/locale'])
    def test_language_list_no_english(self):
        with mock.patch.object(
                forms.gettext_module, 'find',
                side_effect=LanguageTest._patch_gettext_find_all_translated):
            languages = forms._get_languages()
        self.assertEqual(['de', 'ja'],
                         [code for code, name in languages])

    @override_settings(LANGUAGES=(('de', 'Germany'),
                                  ('en', 'English'),
                                  ('ja', 'Japanese')),
                       LOCALE_PATHS=['horizon/locale',
                                     'openstack_dashboard/locale'])
    def test_language_list_with_untranslated_language(self):
        def _patch_gettext_find(*args, **kwargs):
            domain = args[0]
            locale_path = args[1]
            locale = args[2][0]
            # Assume ja is not translated
            if locale == translation.to_locale('ja'):
                return
            return '%s/%s/LC_MESSAGES/%s.mo' % (locale_path, locale, domain)
        with mock.patch.object(
                forms.gettext_module, 'find',
                side_effect=_patch_gettext_find):
            languages = forms._get_languages()
        self.assertEqual(['de', 'en'],
                         [code for code, name in languages])

    @override_settings(LANGUAGES=(('es', 'Spanish'),
                                  ('es-ar', 'Argentinian Spanish'),
                                  ('es-mx', 'Mexican Spanish'),
                                  ('en', 'English')),
                       LOCALE_PATHS=['horizon/locale',
                                     'openstack_dashboard/locale'])
    def test_language_list_with_untranslated_same_prefix(self):
        def _patch_gettext_find(*args, **kwargs):
            domain = args[0]
            locale_path = args[1]
            locale = args[2][0]
            # Assume es-ar is not translated and
            # es-mx is partially translated.
            # es is returned as fallback.
            if locale == translation.to_locale('es-ar'):
                locale = translation.to_locale('es')
            elif (locale == translation.to_locale('es-mx') and
                  locale_path == 'openstack_dashboard/locale'):
                locale = translation.to_locale('es')
            return '%s/%s/LC_MESSAGES/%s.mo' % (locale_path, locale,
                                                domain)
        with mock.patch.object(
                forms.gettext_module, 'find',
                side_effect=_patch_gettext_find):
            languages = forms._get_languages()
        self.assertEqual(['en', 'es'],
                         [code for code, name in languages])

    @override_settings(LANGUAGES=(('en', 'English'),
                                  ('pt', 'Portuguese'),
                                  ('pt-br', 'Brazilian Portuguese')),
                       LOCALE_PATHS=['horizon/locale',
                                     'openstack_dashboard/locale'])
    def test_language_list_with_both_translated_same_prefix(self):
        with mock.patch.object(
                forms.gettext_module, 'find',
                side_effect=LanguageTest._patch_gettext_find_all_translated):
            languages = forms._get_languages()
        self.assertEqual(['en', 'pt', 'pt-br'],
                         [code for code, name in languages])
