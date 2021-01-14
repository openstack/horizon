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

from django.conf import settings
from django.template.defaultfilters import title
from django.utils.translation import ugettext_lazy as _

from horizon import tables
from openstack_dashboard import api
from openstack_dashboard.dashboards.project.api_access import forms
from openstack_dashboard import policy


def pretty_service_names(name):
    name = name.replace('-', ' ')
    if name in ['ec2', 's3']:
        name = name.upper()
    else:
        name = title(name)
    return name


class DownloadEC2(tables.LinkAction):
    name = "download_ec2"
    verbose_name = _("EC2 Credentials")
    verbose_name_plural = _("EC2 Credentials")
    icon = "download"
    url = "horizon:project:api_access:ec2"

    def allowed(self, request, datum=None):
        return api.base.is_service_enabled(request, 'ec2')


class DownloadCloudsYaml(tables.LinkAction):
    name = "download_clouds_yaml"
    verbose_name = _("OpenStack clouds.yaml File")
    verbose_name_plural = _("OpenStack clouds.yaml File")
    icon = "download"
    url = "horizon:project:api_access:clouds.yaml"

    def allowed(self, request, datum=None):
        return settings.SHOW_OPENSTACK_CLOUDS_YAML


class DownloadOpenRC(tables.LinkAction):
    name = "download_openrc"
    verbose_name = _("OpenStack RC File")
    verbose_name_plural = _("OpenStack RC File")
    icon = "download"
    url = "horizon:project:api_access:openrc"

    def allowed(self, request, datum=None):
        return settings.SHOW_OPENRC_FILE


class ViewCredentials(tables.LinkAction):
    name = "view_credentials"
    verbose_name = _("View Credentials")
    classes = ("ajax-modal", )
    icon = "eye"
    url = "horizon:project:api_access:view_credentials"


class RecreateCredentials(tables.LinkAction):
    name = "recreate_credentials"
    verbose_name = _("Recreate EC2 Credentials")
    classes = ("ajax-modal",)
    icon = "refresh"
    url = "horizon:project:api_access:recreate_credentials"
    policy_rules = (("compute", "os_compute_api:certificates:create"))
    action_type = "danger"

    def allowed(self, request, datum=None):
        try:
            target = {"target.credential.user_id": request.user.id}
            if (api.base.is_service_enabled(request, 'ec2') and
                forms.get_ec2_credentials(request) and
                policy.check((("identity", "identity:ec2_create_credential"),
                              ("identity", "identity:ec2_delete_credential")),
                             request, target=target)):
                return True
        except Exception:
            pass
        return False


class EndpointsTable(tables.DataTable):
    api_name = tables.Column('type',
                             verbose_name=_("Service"),
                             filters=(pretty_service_names,))
    api_endpoint = tables.Column('public_url',
                                 verbose_name=_("Service Endpoint"))

    class Meta(object):
        name = "endpoints"
        verbose_name = _("API Endpoints")
        multi_select = False
        table_actions = (ViewCredentials, RecreateCredentials)
        table_actions_menu = (DownloadCloudsYaml,
                              DownloadOpenRC,
                              DownloadEC2)
        table_actions_menu_label = _('Download OpenStack RC File')
