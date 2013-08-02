from django.conf import settings  # noqa
from django.utils.translation import ugettext_lazy as _  # noqa

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

    # URL for additional help with this site.
    'help_url': None,

    # Exception configuration.
    'exceptions': {'unauthorized': [],
                   'not_found': [],
                   'recoverable': []},

    # Password configuration.
    'password_validator': {'regex': '.*',
                           'help_text': _("Password is not accepted")},

    'password_autocomplete': 'on',

    # Enable or disable simplified floating IP address management.
    'simple_ip_management': True
}
