# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.core import urlresolvers
from django.utils.translation import ugettext_lazy as _

from horizon import tables


class ProvidingApplicationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    url = tables.Column(lambda obj: getattr(obj, 'url', None))
    clickable = True
    show_avatar = True

    class Meta:
        name = "providing_table"
        verbose_name = _("Providing Applications")
        multi_select = False
        

class PurchasedApplicationsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    url = tables.Column(lambda obj: getattr(obj, 'url', None))
    clickable = True
    show_avatar = True

    class Meta:
        name = "purchased_table"
        verbose_name = _("Purchased Applications")
        multi_select = False


class ManageAuthorizedMembersLink(tables.LinkAction):
    name = "manage_application_members"
    verbose_name = _("Manage your applications' members")
    url = "horizon:idm:myApplications:members"
    classes = ("ajax-modal",)

    def allowed(self, request, user):
        # TODO(garcianavalon)
        return True

    def get_link_url(self, datum=None):
        app_id = self.table.kwargs['application_id']
        return  urlresolvers.reverse(self.url, args=(app_id,))

class MembersTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Members'))
    show_avatar = True

    class Meta:
        name = "members"
        verbose_name = _("Authorized Members")
        table_actions = (ManageAuthorizedMembersLink, )
        multi_select = False