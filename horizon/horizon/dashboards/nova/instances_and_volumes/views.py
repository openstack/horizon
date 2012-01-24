# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
# Copyright 2011 OpenStack LLC
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

"""
Views for Instances and Volumes.
"""
import logging

from django.contrib import messages
from django.utils.translation import ugettext as _
from django.utils.datastructures import SortedDict
from novaclient import exceptions as novaclient_exceptions

from horizon import api
from horizon import exceptions
from horizon import tables
from .instances.tables import InstancesTable
from .volumes.tables import VolumesTable


LOG = logging.getLogger(__name__)


class IndexView(tables.MultiTableView):
    table_classes = (InstancesTable, VolumesTable)
    template_name = 'nova/instances_and_volumes/index.html'

    def get_instances_data(self):
        # Gather our instances
        try:
            instances = api.server_list(self.request)
        except:
            instances = []
            exceptions.handle(self.request, _('Unable to retrieve instances.'))
        # Gather our flavors and correlate our instances to them
        if instances:
            try:
                flavors = api.flavor_list(self.request)
                full_flavors = SortedDict([(str(flavor.id), flavor) for \
                                            flavor in flavors])
                for instance in instances:
                    instance.full_flavor = full_flavors[instance.flavor["id"]]
            except:
                msg = _('Unable to retrieve instance size information.')
                exceptions.handle(self.request, msg)
        return instances

    def get_volumes_data(self):
        # Gather our volumes
        try:
            volumes = api.volume_list(self.request)
        except novaclient_exceptions.ClientException, e:
            volumes = []
            LOG.exception("ClientException in volume index")
            messages.error(self.request, _('Unable to fetch volumes: %s') % e)
        return volumes
