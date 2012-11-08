# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

import logging

from django import shortcuts
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard import api


LOG = logging.getLogger(__name__)


class DownloadOpenRCForm(forms.SelfHandlingForm):
    tenant = forms.ChoiceField(label=_("Select a Project"))

    def __init__(self, request, *args, **kwargs):
        super(DownloadOpenRCForm, self).__init__(request, *args, **kwargs)
        # Populate tenant choices
        tenant_choices = []
        try:
            tenants = api.tenant_list(request)
        except:
            tenants = []
            exceptions.handle(request, _("Unable to retrieve project list."))
        for tenant in tenants:
            if tenant.enabled:
                tenant_choices.append((tenant.id, tenant.name))
        self.fields['tenant'].choices = tenant_choices

    def handle(self, request, data):
        try:
            tenant_id = data['tenant']
            tenant_name = dict(self.fields['tenant'].choices)[tenant_id]

            keystone_url = api.url_for(request,
                                       'identity',
                                       endpoint_type='publicURL')

            context = {'user': request.user,
                       'auth_url': keystone_url,
                       'tenant_id': tenant_id,
                       'tenant_name': tenant_name}

            response = shortcuts.render(request,
                                        'settings/project/openrc.sh.template',
                                        context,
                                        content_type="text/plain")
            response['Content-Disposition'] = 'attachment; filename=openrc.sh'
            response['Content-Length'] = str(len(response.content))
            return response

        except Exception, e:
            LOG.exception("Exception in DownloadOpenRCForm.")
            messages.error(request, _('Error Downloading RC File: %s') % e)
            return shortcuts.redirect(request.build_absolute_uri())
