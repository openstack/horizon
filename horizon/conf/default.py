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

from django.conf import settings
from django.utils.translation import ugettext_lazy as _

# Default configuration dictionary. Do not mutate.
HORIZON_CONFIG = {
    # Allow for ordering dashboards; list or tuple if provided.
    'dashboards': None,

    # Name of a default dashboard; defaults to first alphabetically if None
    'default_dashboard': None,

    # Default redirect url for users' home
    'user_home': settings.LOGIN_REDIRECT_URL,

    # AJAX settings for JavaScript
    'ajax_queue_limit': 10,
    'ajax_poll_interval': 2500,

    # URL for reporting issue with this site.
    'bug_url': None,

    # URL for additional help with this site.
    'help_url': None,

    # Exception configuration.
    'exceptions': {'unauthorized': [],
                   'not_found': [],
                   'recoverable': []},

    # Password configuration.
    'password_validator': {'regex': '.*',
                           'help_text': _("Password is not accepted")},

    'password_autocomplete': 'off',

    # Enable or disable simplified floating IP address management.
    'simple_ip_management': True
}
