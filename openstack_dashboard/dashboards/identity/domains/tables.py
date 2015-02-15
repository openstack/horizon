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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import defaultfilters as filters
from django.utils.http import urlencode
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy

from keystoneclient import exceptions

from horizon import messages
from horizon import tables

from openstack_dashboard import api

from openstack_dashboard.dashboards.identity.domains import constants


LOG = logging.getLogger(__name__)


class UpdateUsersLink(tables.LinkAction):
    name = "users"
    verbose_name = _("Manage Members")
    url = "horizon:identity:domains:update"
    classes = ("ajax-modal",)
    policy_rules = (("identity", "identity:list_users"),
                    ("identity", "identity:list_roles"),
                    ("identity", "identity:list_role_assignments"))

    def get_link_url(self, domain):
        step = 'update_user_members'
        base_url = reverse(self.url, args=[domain.id])
        param = urlencode({"step": step})
        return "?".join([base_url, param])


class UpdateGroupsLink(tables.LinkAction):
    name = "groups"
    verbose_name = _("Modify Groups")
    url = "horizon:identity:domains:update"
    classes = ("ajax-modal",)
    icon = "pencil"

    def get_link_url(self, domain):
        step = 'update_group_members'
        base_url = reverse(self.url, args=[domain.id])
        param = urlencode({"step": step})
        return "?".join([base_url, param])


class CreateDomainLink(tables.LinkAction):
    name = "create"
    verbose_name = _("Create Domain")
    url = constants.DOMAINS_CREATE_URL
    classes = ("ajax-modal",)
    icon = "plus"
    policy_rules = (('identity', 'identity:create_domain'),)

    def allowed(self, request, domain):
        return api.keystone.keystone_can_edit_domain()


class EditDomainLink(tables.LinkAction):
    name = "edit"
    verbose_name = _("Edit")
    url = constants.DOMAINS_UPDATE_URL
    classes = ("ajax-modal",)
    icon = "pencil"
    policy_rules = (('identity', 'identity:update_domain'),)

    def allowed(self, request, domain):
        return api.keystone.keystone_can_edit_domain()


class DeleteDomainsAction(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            u"Delete Domain",
            u"Delete Domains",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            u"Deleted Domain",
            u"Deleted Domains",
            count
        )

    name = "delete"
    policy_rules = (('identity', 'identity:delete_domain'),)

    def allowed(self, request, datum):
        return api.keystone.keystone_can_edit_domain()

    def delete(self, request, obj_id):
        domain = self.table.get_object_by_id(obj_id)
        if domain.enabled:
            msg = _('Domain "%s" must be disabled before it can be deleted.') \
                % domain.name
            messages.error(request, msg)
            raise exceptions.ClientException(409, msg)
        else:
            LOG.info('Deleting domain "%s".' % obj_id)
            api.keystone.domain_delete(request, obj_id)


class DomainFilterAction(tables.FilterAction):
    def allowed(self, request, datum):
        multidomain_support = getattr(settings,
                                      'OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT',
                                      False)
        return multidomain_support

    def filter(self, table, domains, filter_string):
        """Naive case-insensitive search."""
        q = filter_string.lower()

        def comp(domain):
            if q in domain.name.lower():
                return True
            return False

        return filter(comp, domains)


class SetDomainContext(tables.Action):
    name = "set_domain_context"
    verbose_name = _("Set Domain Context")
    url = constants.DOMAINS_INDEX_URL
    preempt = True
    policy_rules = (('identity', 'admin_required'),)

    def allowed(self, request, datum):
        multidomain_support = getattr(settings,
                                      'OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT',
                                      False)
        if not multidomain_support:
            return False

        ctx = request.session.get("domain_context", None)
        if ctx and datum.id == ctx:
            return False
        return True

    def single(self, table, request, obj_id):
        if ('domain_context' not in request.session or
                request.session['domain_context'] != obj_id):
            try:
                domain = api.keystone.domain_get(request, obj_id)
                request.session['domain_context'] = obj_id
                request.session['domain_context_name'] = domain.name
                messages.success(request,
                                 _('Domain Context updated to Domain %s.') %
                                 domain.name)
            except Exception:
                messages.error(request,
                               _('Unable to set Domain Context.'))


class UnsetDomainContext(tables.Action):
    name = "clear_domain_context"
    verbose_name = _("Clear Domain Context")
    url = constants.DOMAINS_INDEX_URL
    preempt = True
    requires_input = False
    policy_rules = (('identity', 'admin_required'),)

    def allowed(self, request, datum):
        ctx = request.session.get("domain_context", None)
        return ctx is not None

    def single(self, table, request, obj_id):
        if 'domain_context' in request.session:
            request.session.pop("domain_context")
            request.session.pop("domain_context_name")
            messages.success(request, _('Domain Context cleared.'))


class DomainsTable(tables.DataTable):
    name = tables.Column('name', verbose_name=_('Name'))
    description = tables.Column(lambda obj: getattr(obj, 'description', None),
                                verbose_name=_('Description'))
    id = tables.Column('id', verbose_name=_('Domain ID'))
    enabled = tables.Column('enabled', verbose_name=_('Enabled'), status=True,
                            filters=(filters.yesno, filters.capfirst))

    class Meta(object):
        name = "domains"
        verbose_name = _("Domains")
        row_actions = (SetDomainContext, UpdateUsersLink, UpdateGroupsLink,
                       EditDomainLink, DeleteDomainsAction)
        table_actions = (DomainFilterAction, CreateDomainLink,
                         DeleteDomainsAction, UnsetDomainContext)
