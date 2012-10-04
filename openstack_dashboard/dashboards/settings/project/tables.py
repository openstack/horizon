# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
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

from django.utils.translation import ugettext as _

from horizon import tables


def get_endpoint(service):
    return service.endpoints[0]['publicURL']


class EndpointsTable(tables.DataTable):
    api_name = tables.Column('name', verbose_name=_("Service Name"))
    api_endpoint = tables.Column(get_endpoint,
                                 verbose_name=_("Service Endpoint"))

    class Meta:
        name = "endpoints"
        verbose_name = _("API Endpoints")
