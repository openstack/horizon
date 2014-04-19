#    Copyright 2014, NEC Corporation
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

from django.utils.translation import ugettext_lazy as _


def get_monitor_display_name(monitor):
    fields = ['type', 'delay', 'max_retries', 'timeout']
    if monitor.type in ['HTTP', 'HTTPS']:
        fields.extend(['url_path', 'expected_codes', 'http_method'])
        name = _("%(type)s: url:%(url_path)s "
                 "method:%(http_method)s codes:%(expected_codes)s "
                 "delay:%(delay)d retries:%(max_retries)d "
                 "timeout:%(timeout)d")
    else:
        name = _("%(type)s delay:%(delay)d "
                 "retries:%(max_retries)d "
                 "timeout:%(timeout)d")
    params = dict((key, getattr(monitor, key)) for key in fields)
    return name % params
