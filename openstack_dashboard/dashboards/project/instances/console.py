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

import logging

from django.utils.datastructures import SortedDict
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions

from novaclient import exceptions as nova_exception

from openstack_dashboard import api

LOG = logging.getLogger(__name__)

CONSOLES = SortedDict([('VNC', api.nova.server_vnc_console),
                       ('SPICE', api.nova.server_spice_console),
                       ('RDP', api.nova.server_rdp_console),
                       ('SERIAL', api.nova.server_serial_console)])


def get_console(request, console_type, instance):
    """Get a tuple of console url and console type."""
    if console_type == 'AUTO':
        check_consoles = CONSOLES
    else:
        try:
            check_consoles = {console_type: CONSOLES[console_type]}
        except KeyError:
            msg = _('Console type "%s" not supported.') % console_type
            raise exceptions.NotAvailable(msg)

    # Ugly workaround due novaclient API change from 2.17 to 2.18.
    try:
        httpnotimplemented = nova_exception.HttpNotImplemented
    except AttributeError:
        httpnotimplemented = nova_exception.HTTPNotImplemented

    for con_type, api_call in check_consoles.iteritems():
        try:
            console = api_call(request, instance.id)
        # If not supported, don't log it to avoid lot of errors in case
        # of AUTO.
        except httpnotimplemented:
            continue
        except Exception:
            LOG.debug('Console not available', exc_info=True)
            continue

        if con_type == 'SERIAL':
            console_url = console.url
        else:
            console_url = "%s&%s(%s)" % (
                          console.url,
                          urlencode({'title': getattr(instance, "name", "")}),
                          instance.id)

        return (con_type, console_url)

    raise exceptions.NotAvailable(_('No available console found.'))
