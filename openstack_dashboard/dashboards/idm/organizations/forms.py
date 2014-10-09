from django import shortcuts
from django.conf import settings
from django.contrib.auth import authenticate # noqa
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.debug import sensitive_variables  # noqa

import horizon
from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import functions as utils

from openstack_dashboard import api
from openstack_auth import exceptions as auth_exceptions
from openstack_dashboard.api import base
from openstack_dashboard.api import cinder
from openstack_dashboard.api import keystone
from openstack_dashboard.api import nova
from openstack_dashboard.usage import quotas

INDEX_URL = "horizon:idm:organizations:index"
ADD_USER_URL = "horizon:idm:organizations:create_user"
PROJECT_GROUP_ENABLED = keystone.VERSIONS.active >= 3
PROJECT_USER_MEMBER_SLUG = "update_members"
PROJECT_GROUP_MEMBER_SLUG = "update_group_members"

class CreateOrganizationForm(forms.SelfHandlingForm):
	name = forms.CharField(label=_("Name"), max_length=64)
	description = forms.CharField(label=_("Description"),widget=forms.widgets.Textarea, required=False)
	domain_id = forms.CharField(label=_("Domain ID"),required=False,widget=forms.HiddenInput())
	enabled = forms.BooleanField(label=_("Enabled"),required=False,initial=True,widget=forms.HiddenInput())
	domain_name = forms.CharField(label=_("Domain Name"),required=False,widget=forms.HiddenInput())
	

	class Meta:
		name = _("Organization Information")
		help_text = _("Create a new organization. \
            Please enter your organization name and a description. \
            On the next tab, choose the users that will belong to your organization.")
	


	def handle(self, request, data):
    	# create the organization
    		domain_id = data['domain_id']
    	try:
    		desc = data['description']
    		self.object = api.keystone.tenant_create(request,
    												name=data['name'],
    												description=desc,
    												enabled=data['enabled'],
    												domain=domain_id)
    	except Exception:
    		exceptions.handle(request, ignore=True)
    		return False

    	organization_id = self.object.id

    	# update organization members
    	users_to_add = 0
    	try:
    		available_roles = api.keystone.role_list(request)
    		member_step = self.get_step(PROJECT_USER_MEMBER_SLUG)
    		# count how many users are to be added
    		for role in available_roles:
    			field_name = member_step.get_member_field_name(role.id)
    			role_list = data[field_name]
    			users_to_add += len(role_list)
    		# add new users to organization
    		for role in available_roles:
    			field_name = member_step.get_member_field_name(role.id)
    			role_list = data[field_name]
    			users_added = 0
    			for user in role_list:
    				api.keystone.add_tenant_user_role(request,
    													project=organization_id,
    													user=user,
    													role=role.id)
    				users_added += 1
    			users_to_add -= users_added
    	except Exception:
    		if PROJECT_GROUP_ENABLED:
    			group_msg = _(", add organization groups")
    		else:
    			group_msg = ""
    			exceptions.handle(request, _('Failed to add %(users_to_add)s '
    										'organization members%(group_msg)s and '
    										'set organization quotas.')
    										% {'users_to_add': users_to_add,
    										'group_msg': group_msg})
    	if PROJECT_GROUP_ENABLED:
    		# update organization groups
    		groups_to_add = 0
    		try:
    			available_roles = api.keystone.role_list(request)
    			member_step = self.get_step(PROJECT_GROUP_MEMBER_SLUG)

    			# count how many groups are to be added
    			for role in available_roles:
    				field_name = member_step.get_member_field_name(role.id)
    				role_list = data[field_name]
    				groups_to_add += len(role_list)

    			# add new groups to organization
				for role in available_roles:
					field_name = member_step.get_member_field_name(role.id)
					role_list = data[field_name]
					groups_added = 0
					for group in role_list:
						api.keystone.add_group_role(request,
														role=role.id,
														group=group,
														organization=organization_id)
						groups_added += 1
					groups_to_add -= groups_added
			except Exception:
				exceptions.handle(request,
									_('Failed to add %s organization groups '
										'and update organization quotas.')
									% groups_to_add)
			return True
