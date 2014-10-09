# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django import forms
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard.fiware_auth.keystone_manager import KeystoneManager


class RegistrationForm(forms.Form):
    """
    Form for registering a new user account.
    
    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.
    
    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.

    """
    required_css_class = 'required'
    
    username = forms.RegexField(regex=r'^[\w.@+-]+$',
                                max_length=30,
                                label=_("Username"),
                                error_messages={'invalid': _("This value may contain only letters, numbers and @/./+/-/_ characters.")})
    
    email = forms.EmailField(label=_("E-mail"))
    
    password1 = forms.CharField(widget=forms.PasswordInput,
                                label=_("Password"))
    
    password2 = forms.CharField(widget=forms.PasswordInput,
                                label=_("Password (again)"))
    
    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.
        
        """
        username = self.cleaned_data['username']
        #TODO(garcianavalon) check if alphanumeric

        keystone_manager = KeystoneManager()
        existing = keystone_manager.check_user(username)

        if existing.exists():
             raise forms.ValidationError(_("A user with that username already exists."),
                                        code='invalid')
        return username

    def clean_email(self):
        """ Validate taht the email is not already in use"""

        email = self.cleaned_data['email']

        keystone_manager = KeystoneManager()
        existing = keystone_manager.check_email(email)

        if existing.exists():
             raise forms.ValidationError(_("The email is already in use."),
                                         code='invalid')
        return email

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.
        
        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The two password fields didn't match."),
                                                code='invalid')
        return self.cleaned_data


class RequestPasswordResetForm(forms.Form):
    email = forms.EmailField(label=_("E-mail"))
 

class ChangePasswordForm(forms.Form):
    password1 = forms.CharField(widget=forms.PasswordInput,
                                label=_("Password"))
    
    password2 = forms.CharField(widget=forms.PasswordInput,
                                label=_("Confirm password"))

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.
        
        """
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password1'] != self.cleaned_data['password2']:
                raise forms.ValidationError(_("The two password fields didn't match."))
        return self.cleaned_data