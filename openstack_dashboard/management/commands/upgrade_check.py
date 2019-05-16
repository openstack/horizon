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


from __future__ import print_function

import json
import sys

from oslo_upgradecheck import upgradecheck

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy as _


CHECKS = []


def register_check(name):
    def register(func):
        CHECKS.append((name, func))
    return register


@register_check(_("Unknown Settings"))
def check_invalid_settings(dummy=None):
    # This list can be updated using the tools/find_settings.py script.
    KNOWN_SETTINGS = {
        'ABSOLUTE_URL_OVERRIDES', 'ACTION_CSS_CLASSES', 'ADD_INSTALLED_APPS',
        'ADD_TEMPLATE_DIRS', 'ADD_TEMPLATE_LOADERS', 'ADMINS', 'ALLOWED_HOSTS',
        'ALLOWED_PRIVATE_SUBNET_CIDR', 'ANGULAR_FEATURES', 'API_RESULT_LIMIT',
        'API_RESULT_PAGE_SIZE', 'APPEND_SLASH', 'AUTHENTICATION_BACKENDS',
        'AUTHENTICATION_URLS', 'AUTH_PASSWORD_VALIDATORS', 'AUTH_USER_MODEL',
        'AVAILABLE_REGIONS', 'AVAILABLE_THEMES', 'CACHED_TEMPLATE_LOADERS',
        'CACHES', 'CACHE_MIDDLEWARE_ALIAS', 'CACHE_MIDDLEWARE_KEY_PREFIX',
        'CACHE_MIDDLEWARE_SECONDS', 'COMPRESS_CACHEABLE_PRECOMPILERS',
        'COMPRESS_CACHE_BACKEND', 'COMPRESS_CACHE_KEY_FUNCTION',
        'COMPRESS_CLEAN_CSS_ARGUMENTS', 'COMPRESS_CLEAN_CSS_BINARY',
        'COMPRESS_CLOSURE_COMPILER_ARGUMENTS',
        'COMPRESS_CLOSURE_COMPILER_BINARY', 'COMPRESS_CSS_COMPRESSOR',
        'COMPRESS_CSS_FILTERS', 'COMPRESS_CSS_HASHING_METHOD',
        'COMPRESS_DATA_URI_MAX_SIZE', 'COMPRESS_DEBUG_TOGGLE',
        'COMPRESS_ENABLED', 'COMPRESS_JINJA2_GET_ENVIRONMENT',
        'COMPRESS_JS_COMPRESSOR', 'COMPRESS_JS_FILTERS', 'COMPRESS_MINT_DELAY',
        'COMPRESS_MTIME_DELAY', 'COMPRESS_OFFLINE', 'COMPRESS_OFFLINE_CONTEXT',
        'COMPRESS_OFFLINE_MANIFEST', 'COMPRESS_OFFLINE_TIMEOUT',
        'COMPRESS_OUTPUT_DIR', 'COMPRESS_PARSER', 'COMPRESS_PRECOMPILERS',
        'COMPRESS_REBUILD_TIMEOUT', 'COMPRESS_ROOT', 'COMPRESS_STORAGE',
        'COMPRESS_TEMPLATE_FILTER_CONTEXT', 'COMPRESS_URL',
        'COMPRESS_URL_PLACEHOLDER', 'COMPRESS_VERBOSE',
        'COMPRESS_YUGLIFY_BINARY', 'COMPRESS_YUGLIFY_CSS_ARGUMENTS',
        'COMPRESS_YUGLIFY_JS_ARGUMENTS', 'COMPRESS_YUI_BINARY',
        'COMPRESS_YUI_CSS_ARGUMENTS', 'COMPRESS_YUI_JS_ARGUMENTS',
        'CONSOLE_TYPE', 'CREATE_INSTANCE_FLAVOR_SORT', 'CSRF_COOKIE_AGE',
        'CSRF_COOKIE_DOMAIN', 'CSRF_COOKIE_HTTPONLY', 'CSRF_COOKIE_NAME',
        'CSRF_COOKIE_PATH', 'CSRF_COOKIE_SECURE', 'CSRF_FAILURE_VIEW',
        'CSRF_HEADER_NAME', 'CSRF_TRUSTED_ORIGINS', 'CSRF_USE_SESSIONS',
        'DATABASES', 'DATABASE_ROUTERS', 'DATA_UPLOAD_MAX_MEMORY_SIZE',
        'DATA_UPLOAD_MAX_NUMBER_FIELDS', 'DATEPICKER_LOCALES',
        'DATETIME_FORMAT', 'DATETIME_INPUT_FORMATS', 'DATE_FORMAT',
        'DATE_INPUT_FORMATS', 'DEBUG', 'DEBUG_PROPAGATE_EXCEPTIONS',
        'DECIMAL_SEPARATOR', 'DEFAULT_CHARSET', 'DEFAULT_CONTENT_TYPE',
        'DEFAULT_EXCEPTION_REPORTER_FILTER', 'DEFAULT_FILE_STORAGE',
        'DEFAULT_FROM_EMAIL', 'DEFAULT_INDEX_TABLESPACE',
        'DEFAULT_SERVICE_REGIONS', 'DEFAULT_TABLESPACE', 'DEFAULT_THEME',
        'DISALLOWED_USER_AGENTS', 'DROPDOWN_MAX_ITEMS', 'EMAIL_BACKEND',
        'EMAIL_HOST', 'EMAIL_HOST_PASSWORD', 'EMAIL_HOST_USER', 'EMAIL_PORT',
        'EMAIL_SSL_CERTFILE', 'EMAIL_SSL_KEYFILE', 'EMAIL_SUBJECT_PREFIX',
        'EMAIL_TIMEOUT', 'EMAIL_USE_LOCALTIME', 'EMAIL_USE_SSL',
        'EMAIL_USE_TLS', 'ENABLE_CLIENT_TOKEN', 'ENFORCE_PASSWORD_CHECK',
        'EXTERNAL_MONITORING', 'FILE_CHARSET',
        'FILE_UPLOAD_DIRECTORY_PERMISSIONS', 'FILE_UPLOAD_HANDLERS',
        'FILE_UPLOAD_MAX_MEMORY_SIZE', 'FILE_UPLOAD_PERMISSIONS',
        'FILE_UPLOAD_TEMP_DIR', 'FILTER_DATA_FIRST', 'FIRST_DAY_OF_WEEK',
        'FIXTURE_DIRS', 'FORCE_SCRIPT_NAME', 'FORMAT_MODULE_PATH',
        'FORM_RENDERER', 'HORIZON_COMPRESS_OFFLINE_CONTEXT_BASE',
        'HORIZON_CONFIG', 'HORIZON_IMAGES_UPLOAD_MODE', 'IGNORABLE_404_URLS',
        'IMAGES_ALLOW_LOCATION', 'IMAGES_LIST_FILTER_TENANTS',
        'IMAGE_CUSTOM_PROPERTY_TITLES', 'IMAGE_RESERVED_CUSTOM_PROPERTIES',
        'INSTALLED_APPS', 'INSTANCE_LOG_LENGTH', 'INTEGRATION_TESTS_SUPPORT',
        'INTERNAL_IPS', 'KEYSTONE_PROVIDER_IDP_ID',
        'KEYSTONE_PROVIDER_IDP_NAME', 'LANGUAGES', 'LANGUAGES_BIDI',
        'LANGUAGE_CODE', 'LANGUAGE_COOKIE_AGE', 'LANGUAGE_COOKIE_DOMAIN',
        'LANGUAGE_COOKIE_NAME', 'LANGUAGE_COOKIE_PATH',
        'LAUNCH_INSTANCE_DEFAULTS', 'LAUNCH_INSTANCE_LEGACY_ENABLED',
        'LAUNCH_INSTANCE_NG_ENABLED', 'LOCALE_PATHS', 'LOCAL_PATH',
        'LOCAL_SETTINGS_DIR_PATH', 'LOGGING', 'LOGGING_CONFIG', 'LOGIN_ERROR',
        'LOGIN_REDIRECT_URL', 'LOGIN_URL', 'LOGOUT_REDIRECT_URL', 'LOGOUT_URL',
        'MANAGERS', 'MEDIA_ROOT', 'MEDIA_URL', 'MEMOIZED_MAX_SIZE_DEFAULT',
        'MESSAGES_PATH', 'MESSAGE_STORAGE', 'MIDDLEWARE',
        'MIDDLEWARE_CLASSES', 'MIGRATION_MODULES',
        'MONTH_DAY_FORMAT', 'NG_TEMPLATE_CACHE_AGE', 'NUMBER_GROUPING',
        'OPENRC_CUSTOM_TEMPLATE', 'OPENSTACK_API_VERSIONS',
        'OPENSTACK_CINDER_FEATURES', 'OPENSTACK_CLOUDS_YAML_CUSTOM_TEMPLATE',
        'OPENSTACK_CLOUDS_YAML_NAME', 'OPENSTACK_CLOUDS_YAML_PROFILE',
        'OPENSTACK_ENABLE_PASSWORD_RETRIEVE', 'OPENSTACK_ENDPOINT_TYPE',
        'OPENSTACK_HEAT_STACK', 'OPENSTACK_HOST',
        'OPENSTACK_HYPERVISOR_FEATURES', 'OPENSTACK_IMAGE_BACKEND',
        'OPENSTACK_IMAGE_FORMATS', 'OPENSTACK_KEYSTONE_ADMIN_ROLES',
        'OPENSTACK_KEYSTONE_BACKEND', 'OPENSTACK_KEYSTONE_DEFAULT_DOMAIN',
        'OPENSTACK_KEYSTONE_DEFAULT_ROLE',
        'OPENSTACK_KEYSTONE_DOMAIN_DROPDOWN',
        'OPENSTACK_KEYSTONE_FEDERATION_MANAGEMENT',
        'OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT', 'OPENSTACK_KEYSTONE_URL',
        'OPENSTACK_NEUTRON_NETWORK', 'OPENSTACK_PROFILER',
        'OPENSTACK_SSL_CACERT', 'OPENSTACK_SSL_NO_VERIFY',
        'OPERATION_LOG_ENABLED', 'OPERATION_LOG_OPTIONS',
        'OVERVIEW_DAYS_RANGE', 'PASSWORD_HASHERS',
        'PASSWORD_RESET_TIMEOUT_DAYS', 'POLICY_CHECK_FUNCTION', 'POLICY_DIRS',
        'POLICY_FILES', 'POLICY_FILES_PATH', 'PREPEND_WWW',
        'PROJECT_TABLE_EXTRA_INFO', 'REST_API_ADDITIONAL_SETTINGS',
        'REST_API_REQUIRED_SETTINGS', 'ROOT_PATH', 'ROOT_URLCONF',
        'SECONDARY_ENDPOINT_TYPE', 'SECRET_KEY', 'SECURE_BROWSER_XSS_FILTER',
        'SECURE_CONTENT_TYPE_NOSNIFF', 'SECURE_HSTS_INCLUDE_SUBDOMAINS',
        'SECURE_HSTS_PRELOAD', 'SECURE_HSTS_SECONDS',
        'SECURE_PROXY_SSL_HEADER', 'SECURE_REDIRECT_EXEMPT', 'SECURE_SSL_HOST',
        'SECURE_SSL_REDIRECT', 'SECURITY_GROUP_RULES', 'SELECTABLE_THEMES',
        'SERVER_EMAIL', 'SESSION_CACHE_ALIAS', 'SESSION_COOKIE_AGE',
        'SESSION_COOKIE_DOMAIN', 'SESSION_COOKIE_HTTPONLY',
        'SESSION_COOKIE_MAX_SIZE', 'SESSION_COOKIE_NAME',
        'SESSION_COOKIE_PATH', 'SESSION_COOKIE_SECURE', 'SESSION_ENGINE',
        'SESSION_EXPIRE_AT_BROWSER_CLOSE', 'SESSION_FILE_PATH',
        'SESSION_REFRESH', 'SESSION_SAVE_EVERY_REQUEST', 'SESSION_SERIALIZER',
        'SESSION_TIMEOUT', 'SETTINGS_MODULE', 'SHORT_DATETIME_FORMAT',
        'SHORT_DATE_FORMAT', 'SHOW_OPENRC_FILE',
        'SHOW_OPENSTACK_CLOUDS_YAML', 'SIGNING_BACKEND',
        'SILENCED_SYSTEM_CHECKS', 'SITE_BRANDING', 'SITE_BRANDING_LINK',
        'STATICFILES_DIRS', 'STATICFILES_FINDERS', 'STATICFILES_STORAGE',
        'STATIC_ROOT', 'STATIC_URL', 'SWIFT_FILE_TRANSFER_CHUNK_SIZE',
        'TEMPLATES', 'TESTSERVER', 'TEST_GLOBAL_MOCKS_ON_PANELS',
        'TEST_NON_SERIALIZED_APPS', 'TEST_RUNNER', 'THEME_COLLECTION_DIR',
        'THEME_COOKIE_NAME', 'THOUSAND_SEPARATOR', 'TIME_FORMAT',
        'TIME_INPUT_FORMATS', 'TIME_ZONE', 'TOKEN_TIMEOUT_MARGIN',
        'USER_MENU_LINKS', 'USER_TABLE_EXTRA_INFO', 'USE_ETAGS', 'USE_I18N',
        'USE_L10N', 'USE_THOUSAND_SEPARATOR', 'USE_TZ', 'USE_X_FORWARDED_HOST',
        'USE_X_FORWARDED_PORT', 'WEBROOT', 'WEBSSO_CHOICES',
        'WEBSSO_DEFAULT_REDIRECT', 'WEBSSO_DEFAULT_REDIRECT_LOGOUT',
        'WEBSSO_DEFAULT_REDIRECT_PROTOCOL', 'WEBSSO_DEFAULT_REDIRECT_REGION',
        'WEBSSO_ENABLED', 'WEBSSO_IDP_MAPPING', 'WEBSSO_INITIAL_CHOICE',
        'WEBSSO_KEYSTONE_URL', 'WSGI_APPLICATION', 'XSTATIC_MODULES',
        'X_FRAME_OPTIONS', 'YEAR_MONTH_FORMAT',
    }
    invalid = []
    for setting in dir(settings):
        if not setting.isupper() or setting.startswith("_"):
            continue
        if setting not in KNOWN_SETTINGS:
            invalid.append(setting)
    if invalid:
        return upgradecheck.Result(
            upgradecheck.Code.WARNING,
            _("Unknown settings: {}.").format(u", ".join(invalid)),
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
            _("Deprecated settings: {}.").format(u", ".join(deprecated)),
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
            _("Missing required settings: {}.").format(u", ".join(missing)),
        )
    return upgradecheck.Result(upgradecheck.Code.SUCCESS)


class UpgradeCheckTable(upgradecheck.UpgradeCommands):
    _upgrade_checks = CHECKS


class Command(BaseCommand):
    help = _("Perform a check to see if the application is ready for upgrade.")

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
