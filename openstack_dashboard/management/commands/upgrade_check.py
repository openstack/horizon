# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import sys

from oslo_upgradecheck import upgradecheck

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _

from openstack_dashboard import defaults


CHECKS = []


def register_check(name):
    def register(func):
        CHECKS.append((name, func))
    return register


@register_check(_("Unknown Settings"))
def check_invalid_settings(dummy=None):
    # This list can be updated using the tools/find_settings.py script.
    KNOWN_SETTINGS_NON_DASHBOARD = [
        'ABSOLUTE_URL_OVERRIDES',
        'ADD_INSTALLED_APPS',
        'ADD_TEMPLATE_DIRS',
        'ADD_TEMPLATE_LOADERS',
        'ADMINS',
        'ALLOWED_HOSTS',
        'APPEND_SLASH',
        'AUTHENTICATION_BACKENDS',
        'AUTH_PASSWORD_VALIDATORS',
        'AUTH_USER_MODEL',
        'CACHED_TEMPLATE_LOADERS',
        'CACHES',
        'CACHE_MIDDLEWARE_ALIAS',
        'CACHE_MIDDLEWARE_KEY_PREFIX',
        'CACHE_MIDDLEWARE_SECONDS',
        'COMPRESSORS',
        'COMPRESS_CACHEABLE_PRECOMPILERS',
        'COMPRESS_CACHE_BACKEND',
        'COMPRESS_CACHE_KEY_FUNCTION',
        'COMPRESS_CLEAN_CSS_ARGUMENTS',
        'COMPRESS_CLEAN_CSS_BINARY',
        'COMPRESS_CLOSURE_COMPILER_ARGUMENTS',
        'COMPRESS_CLOSURE_COMPILER_BINARY',
        'COMPRESS_CSS_COMPRESSOR',
        'COMPRESS_CSS_FILTERS',
        'COMPRESS_CSS_HASHING_METHOD',
        'COMPRESS_DATA_URI_MAX_SIZE',
        'COMPRESS_DEBUG_TOGGLE',
        'COMPRESS_ENABLED',
        'COMPRESS_FILTERS',
        'COMPRESS_JINJA2_GET_ENVIRONMENT',
        'COMPRESS_JS_COMPRESSOR',
        'COMPRESS_JS_FILTERS',
        'COMPRESS_MINT_DELAY',
        'COMPRESS_MTIME_DELAY',
        'COMPRESS_OFFLINE',
        'COMPRESS_OFFLINE_CONTEXT',
        'COMPRESS_OFFLINE_MANIFEST',
        'COMPRESS_OFFLINE_TIMEOUT',
        'COMPRESS_OUTPUT_DIR',
        'COMPRESS_PARSER',
        'COMPRESS_PRECOMPILERS',
        'COMPRESS_REBUILD_TIMEOUT',
        'COMPRESS_ROOT',
        'COMPRESS_STORAGE',
        'COMPRESS_TEMPLATE_FILTER_CONTEXT',
        'COMPRESS_URL',
        'COMPRESS_URL_PLACEHOLDER',
        'COMPRESS_VERBOSE',
        'COMPRESS_YUGLIFY_BINARY',
        'COMPRESS_YUGLIFY_CSS_ARGUMENTS',
        'COMPRESS_YUGLIFY_JS_ARGUMENTS',
        'COMPRESS_YUI_BINARY',
        'COMPRESS_YUI_CSS_ARGUMENTS',
        'COMPRESS_YUI_JS_ARGUMENTS',
        'CSRF_COOKIE_AGE',
        'CSRF_COOKIE_DOMAIN',
        'CSRF_COOKIE_HTTPONLY',
        'CSRF_COOKIE_NAME',
        'CSRF_COOKIE_PATH',
        'CSRF_COOKIE_SAMESITE',
        'CSRF_COOKIE_SECURE',
        'CSRF_FAILURE_VIEW',
        'CSRF_HEADER_NAME',
        'CSRF_TRUSTED_ORIGINS',
        'CSRF_USE_SESSIONS',
        'DATABASES',
        'DATABASE_ROUTERS',
        'DATA_UPLOAD_MAX_MEMORY_SIZE',
        'DATA_UPLOAD_MAX_NUMBER_FIELDS',
        'DATEPICKER_LOCALES',
        'DATETIME_FORMAT',
        'DATETIME_INPUT_FORMATS',
        'DATE_FORMAT',
        'DATE_INPUT_FORMATS',
        'DEBUG',
        'DEBUG_PROPAGATE_EXCEPTIONS',
        'DECIMAL_SEPARATOR',
        'DEFAULT_CHARSET',
        'DEFAULT_CONTENT_TYPE',
        'DEFAULT_EXCEPTION_REPORTER_FILTER',
        'DEFAULT_FILE_STORAGE',
        'DEFAULT_FROM_EMAIL',
        'DEFAULT_INDEX_TABLESPACE',
        'DEFAULT_TABLESPACE',
        'DISALLOWED_USER_AGENTS',
        'EMAIL_BACKEND',
        'EMAIL_HOST',
        'EMAIL_HOST_PASSWORD',
        'EMAIL_HOST_USER',
        'EMAIL_PORT',
        'EMAIL_SSL_CERTFILE',
        'EMAIL_SSL_KEYFILE',
        'EMAIL_SUBJECT_PREFIX',
        'EMAIL_TIMEOUT',
        'EMAIL_USE_LOCALTIME',
        'EMAIL_USE_SSL',
        'EMAIL_USE_TLS',
        'FILE_CHARSET',
        'FILE_UPLOAD_DIRECTORY_PERMISSIONS',
        'FILE_UPLOAD_HANDLERS',
        'FILE_UPLOAD_MAX_MEMORY_SIZE',
        'FILE_UPLOAD_PERMISSIONS',
        'FILE_UPLOAD_TEMP_DIR',
        'FIRST_DAY_OF_WEEK',
        'FIXTURE_DIRS',
        'FORCE_SCRIPT_NAME',
        'FORMAT_MODULE_PATH',
        'FORM_RENDERER',
        'HORIZON_CONFIG',
        'IGNORABLE_404_URLS',
        'IMAGE_RESERVED_CUSTOM_PROPERTIES',
        'INSTALLED_APPS',
        'INTERNAL_IPS',
        'LANGUAGES',
        'LANGUAGES_BIDI',
        'LANGUAGE_CODE',
        'LANGUAGE_COOKIE_AGE',
        'LANGUAGE_COOKIE_DOMAIN',
        'LANGUAGE_COOKIE_NAME',
        'LANGUAGE_COOKIE_PATH',
        'LOCALE_PATHS',
        'LOCAL_PATH',
        'LOCAL_SETTINGS_DIR_PATH',
        'LOGGING',
        'LOGGING_CONFIG',
        'LOGOUT_REDIRECT_URL',
        'MANAGERS',
        'MESSAGE_STORAGE',
        'MIDDLEWARE',
        'MIDDLEWARE_CLASSES',
        'MIGRATION_MODULES',
        'MONTH_DAY_FORMAT',
        'NUMBER_GROUPING',
        'OPENSTACK_HEAT_STACK',
        'OPENSTACK_HOST',
        'OPENSTACK_IMAGE_FORMATS',
        'PASSWORD_HASHERS',
        'PASSWORD_RESET_TIMEOUT_DAYS',
        'PREPEND_WWW',
        'ROOT_PATH',
        'ROOT_URLCONF',
        'SECRET_KEY',
        'SECURE_BROWSER_XSS_FILTER',
        'SECURE_CONTENT_TYPE_NOSNIFF',
        'SECURE_HSTS_INCLUDE_SUBDOMAINS',
        'SECURE_HSTS_PRELOAD',
        'SECURE_HSTS_SECONDS',
        'SECURE_PROXY_SSL_HEADER',
        'SECURE_REDIRECT_EXEMPT',
        'SECURE_SSL_HOST',
        'SECURE_SSL_REDIRECT',
        'SERVER_EMAIL',
        'SESSION_CACHE_ALIAS',
        'SESSION_COOKIE_AGE',
        'SESSION_COOKIE_DOMAIN',
        'SESSION_COOKIE_HTTPONLY',
        'SESSION_COOKIE_NAME',
        'SESSION_COOKIE_PATH',
        'SESSION_COOKIE_SAMESITE',
        'SESSION_COOKIE_SECURE',
        'SESSION_ENGINE',
        'SESSION_EXPIRE_AT_BROWSER_CLOSE',
        'SESSION_FILE_PATH',
        'SESSION_SAVE_EVERY_REQUEST',
        'SESSION_SERIALIZER',
        'SETTINGS_MODULE',
        'SHORT_DATETIME_FORMAT',
        'SHORT_DATE_FORMAT',
        'SIGNING_BACKEND',
        'SILENCED_SYSTEM_CHECKS',
        'STATICFILES_DIRS',
        'STATICFILES_FINDERS',
        'STATICFILES_STORAGE',
        'TEMPLATES',
        'TESTSERVER',
        'TEST_GLOBAL_MOCKS_ON_PANELS',
        'TEST_NON_SERIALIZED_APPS',
        'TEST_RUNNER',
        'THOUSAND_SEPARATOR',
        'TIME_FORMAT',
        'TIME_INPUT_FORMATS',
        'USE_ETAGS',
        'USE_I18N',
        'USE_L10N',
        'USE_THOUSAND_SEPARATOR',
        'USE_TZ',
        'USE_X_FORWARDED_HOST',
        'USE_X_FORWARDED_PORT',
        'WSGI_APPLICATION',
        'XSTATIC_MODULES',
        'X_FRAME_OPTIONS',
        'YEAR_MONTH_FORMAT',
    ]
    KNOWN_SETTINGS_DASHBOARD = dir(defaults)
    KNOWN_SETTINGS = set(KNOWN_SETTINGS_DASHBOARD +
                         KNOWN_SETTINGS_NON_DASHBOARD)
    invalid = []
    for setting in dir(settings):
        if not setting.isupper() or setting.startswith("_"):
            continue
        if setting not in KNOWN_SETTINGS:
            invalid.append(setting)
    if invalid:
        return upgradecheck.Result(
            upgradecheck.Code.WARNING,
            _("Unknown settings: {}.").format(", ".join(invalid)),
        )
    return upgradecheck.Result(upgradecheck.Code.SUCCESS)


@register_check(_("Deprecated Settings"))
def check_deprecated_settings(dummy=None):
    DEPRECATED_SETTINGS = set()
    deprecated = []
    for setting in dir(settings):
        if not setting.isupper() or setting.startswith("_"):
            continue
        if setting in DEPRECATED_SETTINGS:
            deprecated.append(setting)
    if deprecated:
        return upgradecheck.Result(
            upgradecheck.Code.FAILURE,
            _("Deprecated settings: {}.").format(", ".join(deprecated)),
        )
    return upgradecheck.Result(upgradecheck.Code.SUCCESS)


@register_check(_("Required Settings"))
def check_required_settings(dummy=None):
    REQUIRED_SETTINGS = {
        'ALLOWED_HOSTS',
        'HORIZON_CONFIG',
        'OPENSTACK_KEYSTONE_URL',
    }
    missing = []
    all_settings = set(dir(settings))
    for setting in REQUIRED_SETTINGS:
        if setting not in all_settings:
            missing.append(setting)
    if missing:
        return upgradecheck.Result(
            upgradecheck.Code.FAILURE,
            _("Missing required settings: {}.").format(", ".join(missing)),
        )
    return upgradecheck.Result(upgradecheck.Code.SUCCESS)


@register_check(_("Chinese locale rename"))
def check_chinese_locale_rename(dummy):
    # LANGUAGES setting is defined in Django, so we can assume
    # it always exists.
    langs = [code for code, name in settings.LANGUAGES]
    if 'zh-cn' in langs or 'zh-tw' in langs:
        return upgradecheck.Result(
            upgradecheck.Code.FAILURE,
            _("Chinese locale 'zh-cn' and 'zh-tw' must be renamed to "
              "'zh-hans' and 'zh-hant' respectively in 'LANGUAGES' setting. "
              "If you define them in local_settings.py or local_settings.d "
              "explicitly, ensure to rename them to the new locales.")
        )
    return upgradecheck.Result(upgradecheck.Code.SUCCESS)


class UpgradeCheckTable(upgradecheck.UpgradeCommands):
    _upgrade_checks = CHECKS


class Command(BaseCommand):
    help = "Perform a check to see if the application is ready for upgrade."

    def add_arguments(self, parser):
        parser.add_argument(
            '-f', '--format', choices=['table', 'json'],
            default='table', help=_("The output format")
        )

    def handle(self, *args, **options):
        output_format = options.pop('format')
        final_code = upgradecheck.Code.SUCCESS
        if output_format == 'table':
            final_code = UpgradeCheckTable().check()
        elif output_format == 'json':
            results = []
            for check_name, check_func in CHECKS:
                result = check_func()
                final_code = max(final_code, int(result.code))
                results.append({
                    'check': "{}".format(check_name),
                    'code': int(result.code),
                    'details': "{}".format(result.details),
                })
            print(json.dumps(results))
        sys.exit(final_code)
