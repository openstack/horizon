# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2012 Nebula, Inc.
# Copyright 2012 OpenStack LLC
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
import re
import logging

from django.utils.translation import ugettext_lazy as _
from django.utils.datastructures import SortedDict

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
        if not hasattr(self, "_instances"):
            # Gather our instances
            try:
                instances = self._get_instances()
            except:
                instances = []
                exceptions.handle(self.request,
                                  _('Unable to retrieve instances.'))
            # Gather our flavors and correlate our instances to them
            if instances:
                try:
                    flavors = api.flavor_list(self.request)
                    full_flavors = SortedDict([(str(flavor.id), flavor) for \
                                                flavor in flavors])
                    for instance in instances:
                        flavor_id = instance.flavor["id"]
                        instance.full_flavor = full_flavors[flavor_id]
                except:
                    msg = _('Unable to retrieve instance size information.')
                    exceptions.handle(self.request, msg)
            self._instances = instances
        return self._instances

    def get_volumes_data(self):
        # Gather our volumes
        try:
            volumes = api.volume_list(self.request)
            instances = SortedDict([(inst.id, inst) for inst in
                                    self._get_instances()])
            for volume in volumes:
                # Truncate the description for proper display.
                if len(getattr(volume, 'display_description', '')) > 33:
                    truncated_string = volume.display_description[:30].strip()
                    # Remove non-word, and underscore characters, from the end
                    # of the string before we add the ellepsis.
                    truncated_string = re.sub(ur'[^\w\s]+$',
                                              '',
                                              truncated_string)

                    volume.display_description = truncated_string + u'...'

                for att in volume.attachments:
                    server_id = att.get('server_id', None)
                    att['instance'] = instances.get(server_id, None)
        except:
            volumes = []
            exceptions.handle(self.request,
                              _('Unable to retrieve volume list.'))
        return volumes

    def _get_instances(self):
        if not hasattr(self, "_instances_list"):
            self._instances_list = api.server_list(self.request)
        return self._instances_list
