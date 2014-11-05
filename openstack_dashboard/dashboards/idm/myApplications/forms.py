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

from django import shortcuts
from django.conf import settings
from django import forms
from django.utils.translation import ugettext_lazy as _

from horizon import forms
from horizon.utils import functions as utils


class CreateApplicationForm(forms.SelfHandlingForm):
    name = forms.CharField(label=_("Name"), required=False)
    description = forms.CharField(label=_("Description"), 
                                widget=forms.Textarea, 
                                required=False)
    url = forms.CharField(label=_("URL"), required=False)
    callbackurl = forms.CharField(label=_("Callback URL"), required=False)

    def handle(self, request, data):
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

		x1 = int(x1)
		x2 = int(x2)
		y1 = int(y1)
		y2 = int(y2)

		output_img=img.crop((x1,y1,x2,y2))
		output_img.save(settings.MEDIA_ROOT+"/"+"ApplicationAvatar/"+imageName)

		response = shortcuts.redirect('horizon:idm:myApplications:roles')
		return response

