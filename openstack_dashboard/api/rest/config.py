# Copyright 2015 IBM Corp.
# Copyright 2015, Hewlett-Packard Development Company, L.P.
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

from datetime import datetime

from django.conf import settings
from django.http import JsonResponse
from django.views import generic
import pytz

from openstack_dashboard import api
from openstack_dashboard.api.rest import urls
from openstack_dashboard.api.rest import utils as rest_utils


# settings that we allow to be retrieved via REST API
# these settings are available to the client and are not secured.
# *** THEY SHOULD BE TREATED WITH EXTREME CAUTION ***
settings_required = settings.REST_API_REQUIRED_SETTINGS
settings_additional = settings.REST_API_ADDITIONAL_SETTINGS

settings_allowed = settings_required + settings_additional


@urls.register
class Settings(generic.View):
    """API for retrieving settings.

    This API returns read-only settings values.
    This configuration object can be fetched as needed.
    Examples of settings: OPENSTACK_HYPERVISOR_FEATURES
    """
    url_regex = r'settings/$'
    SPECIALS = {
        'HORIZON_IMAGES_UPLOAD_MODE': api.glance.get_image_upload_mode(),
        'HORIZON_ACTIVE_IMAGE_VERSION': str(api.glance.VERSIONS.active),
        'IMAGES_ALLOW_LOCATION': settings.IMAGES_ALLOW_LOCATION,
        'AJAX_POLL_INTERVAL': settings.HORIZON_CONFIG.get(
            'ajax_poll_interval', 2500)
    }

    @rest_utils.ajax()
    def get(self, request):
        # TODO(amotoki): Drop the default value of getattr.
        # It will be unnecessary once all default settings are defined.
        plain_settings = {k: getattr(settings, k, None) for k
                          in settings_allowed if k not in self.SPECIALS}
        plain_settings.update(self.SPECIALS)
        plain_settings.update(self.disk_formats(request))
        return plain_settings

    def disk_formats(self, request):
        # The purpose of OPENSTACK_IMAGE_FORMATS is to provide a simple object
        # that does not contain the lazy-loaded translations, so the list can
        # be sent as JSON to the client-side (Angular).
        return {'OPENSTACK_IMAGE_FORMATS': [
            value
            for (value, name) in api.glance.get_image_formats(request)
        ]}


@urls.register
class Timezones(generic.View):
    """API for timezone service."""
    url_regex = r'timezones/$'

    @rest_utils.ajax()
    def get(self, request):
        zones = {tz: datetime.now(pytz.timezone(tz)).strftime('%z')
                 for tz in pytz.common_timezones}
        return JsonResponse({'timezone_dict': zones})
