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

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from horizon import forms

from openstack_dashboard import api
from openstack_dashboard.dashboards.project.routers import forms as r_forms


class CreateForm(r_forms.CreateForm):
    tenant_id = forms.ThemableChoiceField(label=_("Project"))
    # Other fields which are not defined in field_order will be
    # placed in the default order.
    field_order = ['name', 'tenant_id']
    failure_url = 'horizon:admin:routers:index'

    def __init__(self, request, *args, **kwargs):
        super(CreateForm, self).__init__(request, *args, **kwargs)
        tenant_choices = [('', _("Select a project"))]
        tenants, __ = api.keystone.tenant_list(request)
        for tenant in tenants:
            if tenant.enabled:
                tenant_choices.append((tenant.id, tenant.name))
        self.fields['tenant_id'].choices = tenant_choices


class UpdateForm(r_forms.UpdateForm):
    redirect_url = reverse_lazy('horizon:admin:routers:index')
