# Copyright (C) 2014 Universidad Politecnica de Madrid
#
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

from django import forms 
from PIL import Image

class ImageCropMixin(forms.Form):
    x1 = forms.DecimalField(widget=forms.HiddenInput(), required=False)
    y1 = forms.DecimalField(widget=forms.HiddenInput(), required=False)
    x2 = forms.DecimalField(widget=forms.HiddenInput(), required=False)
    y2 = forms.DecimalField(widget=forms.HiddenInput(), required=False)

    def crop(self, image):
        x1 = int(self.cleaned_data['x1'])
        x2 = int(self.cleaned_data['x2'])
        y1 = int(self.cleaned_data['y1'])
        y2 = int(self.cleaned_data['y2'])

        img = Image.open(image)
        output_img = img.crop((x1, y1, x2, y2))

        return output_img