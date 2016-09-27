import horizon

from django.db import transaction
from django.db import IntegrityError
from django.utils.translation import ugettext_lazy as _

from horizon import forms

from openstack_dashboard.dashboards.identity.projects import views as project_views
from openstack_dashboard.dashboards.identity.projects import workflows as project_workflows
from openstack_dashboard.dashboards.project.access_and_security import api_access
from openstack_dashboard.dashboards.project.access_and_security.api_access import views as api_access_views
from openstack_dashboard import api

import json
import requests

COMMON_HORIZONTAL_TEMPLATE = "identity/projects/_common_horitonztal_form.html"

# TODO add deleteProject override

# extends workflows.Step
class IronCreateProjectQuota(project_workflows.CreateProjectQuota):
    template_name = COMMON_HORIZONTAL_TEMPLATE
    depends_on = ('iron_user_id', 'iron_token', 'iron_auth_url')

# extends workflows.Action
class IronCreateProjectInfoAction(project_workflows.CreateProjectInfoAction):

    def __init__(self, request, *args, **kwargs):
        super(IronCreateProjectInfoAction, self).__init__(request, *args, **kwargs)

        self.fields['iron_user_id'] = forms.CharField(
                                        label=_("Iron User ID"),
                                        required=True
        )
        self.fields['iron_token'] = forms.CharField(
                                    label=_("Iron API Token"),
                                    required=True
                                    )
        self.fields['iron_auth_url'] = forms.CharField(
                                        label=_("Iron Auth URL"),
                                        initial="https://auth.iron.io",
                                        required=True
                                    )

    class Meta:
        name = _("Project Info")
        help_text = _("From here you can create a new Iron.io project to run on OpenStack.")

project_workflows.CreateProjectInfo.action_class = IronCreateProjectInfoAction

# extends workflows.Step
class IronCreateProjectInfo(project_workflows.CreateProjectInfo):
    action_class = IronCreateProjectInfoAction
    template_name = COMMON_HORIZONTAL_TEMPLATE
    contributes = ("domain_id",
                    "domain_name",
                    "project_id",
                    "name",
                    "description",
                    "enabled",
                    "iron_user_id",
                    "iron_token",
                    "iron_auth_url")

# for some reason this seems necessary, too
project_workflows.CreateProjectInfo.contributes = ("domain_id",
                    "domain_name",
                    "project_id",
                    "name",
                    "description",
                    "enabled",
                    "iron_user_id",
                    "iron_token",
                    "iron_auth_url")

# extends workflows.Workflow
class IronCreateProject(project_workflows.CreateProject):
    finalize_button_name = _("Create Iron Project") # easy way to see if this class is being used

    # for data to be passed in from another step, the step needs to contribute data and the steps
    # need to be ordered properly
    def __init__(self, request=None, context_seed=None, entry_point=None, *args, **kwargs):

        self.default_steps = (IronCreateProjectInfo,
                                project_workflows.UpdateProjectMembers,
                                project_workflows.UpdateProjectGroups,
                                IronCreateProjectQuota)

        super(IronCreateProject, self).__init__(request=request,
                                        context_seed=context_seed,
                                        entry_point=entry_point,
                                        *args,
                                        **kwargs)

    def handle(self, request, data):
        name = data['name']
        desc = data['description']
        iron_user_id = data['iron_user_id']
        iron_token = data['iron_token']
        iron_auth_url = data['iron_auth_url']

        try:
            super(IronCreateProject, self).handle(request, data)

            headers = {'Authorization': 'OAuth ' + iron_token}
            url = iron_auth_url + '/2/authentication'

            response = requests.get(url, headers=headers)
            # TODO /2/authentication should return tenant_id but isn't, see why that is.
            if response.status_code == 200:
                # fetch (Iron) tenant_id from auth in another call until fixed.
                url = iron_auth_url + '/2/users/' + iron_user_id
                response = requests.get(url, headers=headers)

                if response.status_code == 200:
                    result = response.json()
                    tenant_id = result['user']['tenant_ids'][0]

                    payload = {'name':name,'tenant_id':tenant_id}
                    headers['Content-Type'] = 'application/json'
                    url = iron_auth_url + '/2/projects'

                    response = requests.post(url, data=json.dumps(payload), headers=headers)

                    if response.status_code == 200:
                        # FIXME do something with project_id and iron_token to display to user.
                        # result = response.json()
                        # iron_project_id = result['project']['id']

                        # TODO display iron_project_id and iron_token to user
                        # Adding this info to the API Access panel requires a way to store and display
                        # credentials via Keystone. This is one milestone for Keystone integration and
                        # can be added later, for instance as a python-keystoneclient module similar to
                        # the EC2 module which represents an EC2 resource.

                    else:
                        horizon.exceptions.handle(request,
                                                    _("Failed to create Iron project."))
                else:
                    horizon.exceptions.handle(request,
                                                _("Failed to fetch tenant_id."))
            else:
                horizon.exceptions.handle(request,
                                            _('Failed to validate Iron API Token.'))
        except Exception:
            horizon.exceptions.handle(request,
                                        _('Could not create project.'))
        return True

project_views.CreateProjectView.workflow_class = IronCreateProject