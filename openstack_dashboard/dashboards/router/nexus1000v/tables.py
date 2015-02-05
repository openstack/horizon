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

from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from horizon import exceptions
from horizon import tables

from openstack_dashboard import api

LOG = logging.getLogger(__name__)


class CreateNetworkProfile(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Network Profile")
    url = "horizon:router:nexus1000v:create_network_profile"
    classes = ("ajax-modal",)
    icon = "plus"


class DeleteNetworkProfile(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Network Profile",
            u"Delete Network Profiles",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Network Profile",
            u"Deleted Network Profiles",
            count
        )

    def delete(self, request, obj_id):
        try:
            api.neutron.profile_delete(request, obj_id)
        except Exception:
            msg = _('Failed to delete network profile (%s).') % obj_id
            LOG.info(msg)
            redirect = reverse('horizon:router:nexus1000v:index')
            exceptions.handle(request, msg, redirect=redirect)


class EditNetworkProfile(tables.LinkAction):
    name = "update"
    verbose_name = _("Edit Network Profile")
    url = "horizon:router:nexus1000v:update_network_profile"
    classes = ("ajax-modal",)
    icon = "pencil"


class NetworkProfile(tables.DataTable):
    id = tables.Column("id", hidden=True)
    name = tables.Column("name", verbose_name=_("Network Profile"), )
    project = tables.Column("project_name", verbose_name=_("Project"))
    segment_type = tables.Column("segment_type",
                                 verbose_name=_("Segment Type"))
    sub_type = tables.Column("sub_type",
                             verbose_name=_("Sub Type"))
    segment_range = tables.Column("segment_range",
                                  verbose_name=_("Segment Range"))
    multicast_ip_range = tables.Column("multicast_ip_range",
                                       verbose_name=_("Multicast IP Range"))
    physical_network = tables.Column("physical_network",
                                     verbose_name=_("Physical Network Name"))

    class Meta(object):
        name = "network_profile"
        verbose_name = _("Network Profile")
        table_actions = (CreateNetworkProfile, DeleteNetworkProfile,)
        row_actions = (EditNetworkProfile, DeleteNetworkProfile,)


class PolicyProfile(tables.DataTable):
    id = tables.Column("id", hidden=True)
    name = tables.Column("name", verbose_name=_("Policy Profile"), )
    project = tables.Column("project_name", verbose_name=_("Project"))

    class Meta(object):
        name = "policy_profile"
        verbose_name = _("Policy Profile")
