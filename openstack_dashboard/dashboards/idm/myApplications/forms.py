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



CHOICES=[('role1','Role 1'),
         ('role2','Role 2'),
         ('role3','Role 3' )]


class CreateApplicationForm(forms.SelfHandlingForm):
	name = forms.CharField(label=_("Name"), required=False)
	description = forms.CharField(label=_("Description"),widget=forms.Textarea, required=False)
	url = forms.CharField(label=_("URL"), required=False)
	callbackurl = forms.CharField(label=_("Callback URL"), required=False)

	def handle(self, request,data):
		response = shortcuts.redirect('horizon:idm:myApplications:upload')
		return response
	
class UploadImageForm(forms.SelfHandlingForm):
	image = forms.ImageField(required=True)
		
	def handle(self, request, data):
		print(request.FILES['image'])
		image = request.FILES['image']
		imageName = image.name
		with open(settings.MEDIA_ROOT+'/'+imageName, 'wb+') as destination:
			for chunk in image.chunks():
				destination.write(chunk)
		response = shortcuts.redirect('horizon:idm:myApplications:roles')
		return response
	
class RolesApplicationForm(forms.SelfHandlingForm):
	role = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)

	def handle(self, request, data):
		response = shortcuts.redirect('horizon:idm:myApplications:index')
		return response

