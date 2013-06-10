# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Hewlett-Packard Development Company, L.P.
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

from django.utils.translation import ugettext_lazy as _

from keystoneclient.exceptions import ClientException

from horizon import messages
from horizon import tables

from openstack_dashboard import api

from .constants import DOMAINS_CREATE_URL
from .constants import DOMAINS_UPDATE_URL


LOG = logging.getLogger(__name__)


class CreateDomainLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Domain")
    url = DOMAINS_CREATE_URL
    classes = ("ajax-modal", "btn-create")

    def allowed(self, request, domain):
        return api.keystone.keystone_can_edit_domain()


class EditDomainLink(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = DOMAINS_UPDATE_URL
    classes = ("ajax-modal", "btn-edit")

    def allowed(self, request, domain):
        return api.keystone.keystone_can_edit_domain()


class DeleteDomainsAction(tables.DeleteAction):
    name = "delete"
    data_type_singular = _("Domain")
    data_type_plural = _("Domains")

    def allowed(self, request, datum):
        return api.keystone.keystone_can_edit_domain()

    def delete(self, request, obj_id):
        domain = self.table.get_object_by_id(obj_id)
        if domain.enabled:
            msg = _('Domain "%s" must be disabled before it can be deleted.') \
                % domain.name
            messages.error(request, msg)
            raise ClientException(409, msg)
        else:
            LOG.info('Deleting domain "%s".' % obj_id)
            api.keystone.domain_delete(request, obj_id)


class DomainFilterAction(tables.FilterAction):
    def filter(self, table, domains, filter_string):
        """ Naive case-insensitive search """
        q = filter_string.lower()

        def comp(domain):
            if q in domain.name.lower():
                return True
            return False

        return filter(comp, domains)


class DomainsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'))
    id = tables.Column('id', verbose_name=_('Domain ID'))
    enabled = tables.Column('enabled', verbose_name=_('Enabled'), status=True)

    class Meta:
        name = "domains"
        verbose_name = _("Domains")
        row_actions = (EditDomainLink, DeleteDomainsAction)
        table_actions = (DomainFilterAction, CreateDomainLink,
                         DeleteDomainsAction)
