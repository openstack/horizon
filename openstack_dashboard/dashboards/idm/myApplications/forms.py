from django import shortcuts
from django.conf import settings
from django import forms 
from django.utils.translation import ugettext_lazy as _

from horizon import exceptions
from horizon import forms
from horizon import messages
from horizon.utils import functions as utils
from openstack_dashboard import api
from openstack_auth import exceptions as auth_exceptions
from PIL import Image 

import os


CHOICES=[('role1','Role 1'),
         ('role2','Role 2'),
         ('role3','Role 3' )]

DEFAULT_AVATAR = os.path.abspath(os.path.join(settings.ROOT_PATH, '..', 'openstack_dashboard/static/dashboard/img/logos/original/group.png'))


class CreateApplicationForm(forms.SelfHandlingForm):
	name = forms.CharField(label=_("Name"), required=False)
	description = forms.CharField(label=_("Description"),widget=forms.Textarea, required=False)
	url = forms.CharField(label=_("URL"), required=False)
	callbackurl = forms.CharField(label=_("Callback URL"), required=False)

	def handle(self, request,data):
		response = shortcuts.redirect('horizon:idm:myApplications:upload')
		return response
	
class UploadImageForm(forms.SelfHandlingForm):
	image = forms.ImageField(required=False)
	x1 = forms.DecimalField(widget=forms.HiddenInput(), required=False)
	y1 = forms.DecimalField(widget=forms.HiddenInput(),required=False)
	x2 = forms.DecimalField(widget=forms.HiddenInput(),required=False)
	y2 = forms.DecimalField(widget=forms.HiddenInput(),required=False)
		
	def handle(self, request, data):
		if request.FILES:
			x1=self.cleaned_data['x1'] 
			x2=self.cleaned_data['x2']
			y1=self.cleaned_data['y1']
			y2=self.cleaned_data['y2']
					
			image = request.FILES['image'] 
			imageName = image.name
			
			img = Image.open(image)

			x1 = int(x1)
			x2 = int(x2)
			y1 = int(y1)
			y2 = int(y2)

			output_img=img.crop((x1,y1,x2,y2))
		else:
			output_img = Image.open(DEFAULT_AVATAR)
			imageName = 'avatarApp'
			
		output_img.save(settings.MEDIA_ROOT+"/"+"ApplicationAvatar/"+imageName, 'JPEG')

		response = shortcuts.redirect('horizon:idm:myApplications:roles')
		return response
	
class RolesApplicationForm(forms.SelfHandlingForm):
	role = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)

	def handle(self, request, data):
		response = shortcuts.redirect('horizon:idm:myApplications:index')
		return response

