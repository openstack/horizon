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

from horizon import exceptions
from horizon import forms
from horizon import workflows

from openstack_dashboard import api

from openstack_dashboard.dashboards.admin.domains.constants \
    import DOMAINS_INDEX_URL

LOG = logging.getLogger(__name__)


class CreateDomainInfoAction(workflows.Action):
    name = forms.CharField(label=_("Name"),
                           required=True)
    description = forms.CharField(widget=forms.widgets.Textarea(),
                                  label=_("Description"),
                                  required=False)
    enabled = forms.BooleanField(label=_("Enabled"),
                                 required=False,
                                 initial=True)

    class Meta:
        name = _("Domain Info")
        slug = "create_domain"
        help_text = _("From here you can create a new domain to organize "
                      "projects, groups and users.")


class CreateDomainInfo(workflows.Step):
    action_class = CreateDomainInfoAction
    contributes = ("domain_id",
                   "name",
                   "description",
                   "enabled")


class CreateDomain(workflows.Workflow):
    slug = "create_domain"
    name = _("Create Domain")
    finalize_button_name = _("Create Domain")
    success_message = _('Created new domain "%s".')
    failure_message = _('Unable to create domain "%s".')
    success_url = DOMAINS_INDEX_URL
    default_steps = (CreateDomainInfo, )

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown domain')

    def handle(self, request, data):
        # create the domain
        try:
            LOG.info('Creating domain with name "%s"' % data['name'])
            desc = data['description']
            api.keystone.domain_create(request,
                                       name=data['name'],
                                       description=desc,
                                       enabled=data['enabled'])
        except Exception:
            exceptions.handle(request, ignore=True)
            return False

        return True


class UpdateDomainInfoAction(CreateDomainInfoAction):

    class Meta:
        name = _("Domain Info")
        slug = 'update_domain'
        help_text = _("From here you can edit the domain details.")


class UpdateDomainInfo(workflows.Step):
    action_class = UpdateDomainInfoAction
    depends_on = ("domain_id",)
    contributes = ("name",
                   "description",
                   "enabled")


class UpdateDomain(workflows.Workflow):
    slug = "update_domain"
    name = _("Edit Domain")
    finalize_button_name = _("Save")
    success_message = _('Modified domain "%s".')
    failure_message = _('Unable to modify domain "%s".')
    success_url = DOMAINS_INDEX_URL
    default_steps = (UpdateDomainInfo, )

    def format_status_message(self, message):
        return message % self.context.get('name', 'unknown domain')

    def handle(self, request, data):
        domain_id = data.pop('domain_id')

        try:
            LOG.info('Updating domain with name "%s"' % data['name'])
            api.keystone.domain_update(request,
                                       domain_id=domain_id,
                                       name=data['name'],
                                       description=data['description'],
                                       enabled=data['enabled'])
        except Exception:
            exceptions.handle(request, ignore=True)
            return False
        return True
