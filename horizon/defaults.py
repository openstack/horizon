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

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from openstack_auth.defaults import *  # noqa: F403,H303

from horizon.contrib import bootstrap_datepicker

# From Django
# DEBUG
# LOGIN_URL
# LOGIN_REDIRECT_URL
# STATIC_URL
# CSRF_COOKIE_HTTPONLY = False
# SESSION_ENGINE
# SESSION_COOKIE_NAME

# Django default value of TIME_ZONE is America/Chicago for backward
# compatibility, so we should define this explicitly.
TIME_ZONE = 'UTC'

# ----------------------------------------
# horizon settings
# ----------------------------------------

# TODO(amotoki): Break down into the usage of ROOT_PATH?
# It seems ROOT_PATH is used for various purposes.
# ROOT_PATH

WEBROOT = '/'
LOGOUT_URL = WEBROOT + 'auth/logout/'

POLICY_CHECK_FUNCTION = None
INTEGRATION_TESTS_SUPPORT = False
NG_TEMPLATE_CACHE_AGE = 0
# Control whether the SESSION_TIMEOUT period is refreshed due to activity. If
# False, SESSION_TIMEOUT acts as a hard limit.
SESSION_REFRESH = True
# When using cookie-based sessions, log error when the session cookie exceeds
# the following size (common browsers drop cookies above a certain size):
SESSION_COOKIE_MAX_SIZE = 4093
# MEMOIZED_MAX_SIZE_DEFAULT allows setting a global default to help control
# memory usage when caching. It should at least be 2 x the number of threads
# with a little bit of extra buffer.
MEMOIZED_MAX_SIZE_DEFAULT = 25
HORIZON_COMPRESS_OFFLINE_CONTEXT_BASE = {}

SITE_BRANDING = _("Horizon")
SITE_BRANDING_LINK = reverse_lazy("horizon:user_home")

DATEPICKER_LOCALES = bootstrap_datepicker.LOCALE_MAPPING

# For Bootstrap integration; can be overridden in settings.
ACTION_CSS_CLASSES = ()

SELECTABLE_THEMES = []
# TODO(amotoki): How can we define the default value for this?
# AVAILABLE_THEMES
THEME_COLLECTION_DIR = 'themes'
THEME_COOKIE_NAME = 'theme'
DEFAULT_THEME = 'default'

OPERATION_LOG_ENABLED = False
OPERATION_LOG_OPTIONS = {
    'mask_fields': ['password', 'current_password',
                    'new_password', 'confirm_password'],
    'target_methods': ['POST'],
    'ignore_urls': ['/js/', '/static/', '^/api/'],
    'format': (
        "[%(client_ip)s] [%(domain_name)s]"
        " [%(domain_id)s] [%(project_name)s]"
        " [%(project_id)s] [%(user_name)s] [%(user_id)s]"
        " [%(request_scheme)s] [%(referer_url)s] [%(request_url)s]"
        " [%(message)s] [%(method)s] [%(http_status)s] [%(param)s]"
    ),
}

OPENSTACK_PROFILER = {
    'enabled': False,
    'facility_name': 'horizon',
    'keys': [],
    'receiver_connection_string': "mongodb://",
    'notifier_connection_string': None,
}
