from django import shortcuts
from django.conf import settings
from django import forms 
from django.utils.translation import ugettext_lazy as _

import horizon
from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import functions as utils
from openstack_dashboard import api
from openstack_auth import exceptions as auth_exceptions
from openstack_dashboard.api import keystone


class CreateOrganizationForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"), max_length=64,required=True)
    description = forms.CharField(label=_("Description"),widget=forms.widgets.Textarea, required=True)
    domain_id = forms.CharField(label=_("Domain ID"),required=False,widget=forms.HiddenInput())
    enabled = forms.BooleanField(label=_("Enabled"),required=False,initial=True,widget=forms.HiddenInput())
    domain_name = forms.CharField(label=_("Domain Name"),required=False,widget=forms.HiddenInput())

    def handle(self, request,data):
    	#create organization
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

    	#Set organization and user id
    	organization_id = self.object.id
    	user_id = request.user.id
    	user = api.keystone.user_get(request, user_id, admin=False)

    	#Find default role id
    	try:
    		default_role = api.keystone.get_default_role(self.request)
    		if default_role is None:
    			default = getattr(settings,
    								"OPENSTACK_KEYSTONE_DEFAULT_ROLE", None)
    			msg = _('Could not find default role "%s" in Keystone') % \
    					default
    			raise exceptions.NotFound(msg)
    	except Exception:
    		exceptions.handle(self.request, 
    							err_msg,
    							redirect=reverse('horizon:idm:organizations:index'))
    		return False
    	try:
    		api.keystone.add_tenant_user_role(request,
    										project=organization_id,
    										user=user_id,
    										role=default_role.id)
    	except Exception:
    		exceptions.handle(request,
    								_('Failed to add %s organization to list')
    								% data['name'])
    		return False
    
       	response = shortcuts.redirect('horizon:idm:organizations:index')
    	return response

class EditOrganizationForm(forms.SelfHandlingForm):
    id = forms.CharField(label=_("ID"), widget=forms.HiddenInput)
    name = forms.CharField(label=_("Name"), max_length=64,required=False)
    description = forms.CharField(label=_("Description"),widget=forms.widgets.Textarea, required=False)

    def handle(self, request, data):
        try:
            api.keystone.tenant_update(request, data['id'], name=data['name'], description=data['description'])
            messages.success(request, _("Organization updated successfully."))
            response = shortcuts.redirect('horizon:idm:organizations:index')
            return response
        except Exception:
            exceptions.handle(request, _('Unable to update organization.'))

       

