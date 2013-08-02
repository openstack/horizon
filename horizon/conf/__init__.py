import copy

from django.utils.functional import empty  # noqa
from django.utils.functional import LazyObject  # noqa


class LazySettings(LazyObject):
    def _setup(self, name=None):
        from django.conf import settings  # noqa
        from horizon.conf.default import HORIZON_CONFIG as DEFAULT_CONFIG  # noqa
        HORIZON_CONFIG = copy.copy(DEFAULT_CONFIG)
        HORIZON_CONFIG.update(settings.HORIZON_CONFIG)

        # Ensure we always have our exception configuration...
        for exc_category in ['unauthorized', 'not_found', 'recoverable']:
            if exc_category not in HORIZON_CONFIG['exceptions']:
                default_exc_config = DEFAULT_CONFIG['exceptions'][exc_category]
                HORIZON_CONFIG['exceptions'][exc_category] = default_exc_config

        # Ensure our password validator always exists...
        if 'regex' not in HORIZON_CONFIG['password_validator']:
            default_pw_regex = DEFAULT_CONFIG['password_validator']['regex']
            HORIZON_CONFIG['password_validator']['regex'] = default_pw_regex
        if 'help_text' not in HORIZON_CONFIG['password_validator']:
            default_pw_help = DEFAULT_CONFIG['password_validator']['help_text']
            HORIZON_CONFIG['password_validator']['help_text'] = default_pw_help

        self._wrapped = HORIZON_CONFIG

    def __getitem__(self, name, fallback=None):
        if self._wrapped is empty:
            self._setup(name)
        return self._wrapped.get(name, fallback)

HORIZON_CONFIG = LazySettings()
