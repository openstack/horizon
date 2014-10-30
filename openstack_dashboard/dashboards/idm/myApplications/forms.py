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
	x1 = forms.DecimalField(widget=forms.HiddenInput(), required=False)
	y1 = forms.DecimalField(widget=forms.HiddenInput(),required=False)
	x2 = forms.DecimalField(widget=forms.HiddenInput(),required=False)
	y2 = forms.DecimalField(widget=forms.HiddenInput(),required=False)
		
	def handle(self, request, data):
		x1=self.cleaned_data['x1'] 
		x2=self.cleaned_data['x2']
		y1=self.cleaned_data['y1']
		y2=self.cleaned_data['y2']
				
		
		image = request.FILES['image'] 
		imageName = image.name
		
		img = Image.open(image)

		if x1 > x2:
			left = x2
			right = x1
		else:
			left = x1
			right = x2
		if y1 > y2:
			bottom = y2
			top = y1
		else:
			bottom = y1
			top = y2

		output_img=img.crop((x1,y1,x2,y2))
		output_img.save(settings.MEDIA_ROOT+"/"+"ApplicationAvatar/"+imageName)

		# import pdb
		# pdb.set_trace()
		

		response = shortcuts.redirect('horizon:idm:myApplications:roles')
		return response
	
class RolesApplicationForm(forms.SelfHandlingForm):
	role = forms.ChoiceField(choices=CHOICES, widget=forms.RadioSelect)

	def handle(self, request, data):
		response = shortcuts.redirect('horizon:idm:myApplications:index')
		return response

