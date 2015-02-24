# Copyright 2015 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.views import generic

from horizon import conf

from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils


# properties we know are admin config
admin_configs = ['ajax_queue_limit', 'ajax_poll_interval',
                 'user_home', 'help_url',
                 'password_autocomplete', 'disable_password_reveal']

# properties we know are user config
# this is a white list of keys under HORIZON_CONFIG in settings.pys
# that we want to pass onto client
user_configs = ['auto_fade_alerts', 'modal_backdrop']


@urls.register
class DefaultUserConfigs(generic.View):
    """API for retrieving user configurations.

    This API returns read-only-default configuration values.
    This configuration object is ideally fetched once per application life
    or when a user needs to restore the default values.
    Examples of user config: modal_backdrop, disable_password_reveal
    """
    url_regex = r'config/user/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get default user configurations
        """
        config = {}
        for key in user_configs:
            config[key] = conf.HORIZON_CONFIG.get(key, None)
        return config


@urls.register
class AdminConfigs(generic.View):
    """API for retrieving admin configurations.

    This API returns read-only admin configuration values.
    This configuration object can be fetched as needed.
    Examples of admin config: help_url, user_home
    """
    url_regex = r'config/admin/$'

    @rest_utils.ajax()
    def get(self, request):
        """Get read-only admin configurations
        """
        config = {}
        for key in admin_configs:
            config[key] = conf.HORIZON_CONFIG.get(key, None)
        return config
