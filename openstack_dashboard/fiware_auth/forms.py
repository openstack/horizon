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
from keystoneclient import exceptions as keystoneclient_exceptions   

from openstack_dashboard.fiware_auth.keystone_manager import KeystoneManager

class ConfirmPasswordForm(forms.Form):
    """Encapsulates the idea of two password fields and checking they are the same"""
    password1 = forms.CharField(widget=forms.PasswordInput,
                                label=_("Password"))
    
    password2 = forms.CharField(widget=forms.PasswordInput,
                                label=_("Password (again)"))

    def clean(self):
        """
        Verifiy that the values entered into the two password fields
        match. Note that an error here will end up in
        ``non_field_errors()`` because it doesn't apply to a single
        field.
        
        """
        data = super(ConfirmPasswordForm, self).clean()

        if data['password1'] != data['password2']:
            raise forms.ValidationError(_("The two password fields didn't match."),
                                            code='invalid')
        return data

class RegistrationForm(ConfirmPasswordForm):
    """
    Form for registering a new user account.
    
    Validates that the requested username is not already in use, and
    requires the password to be entered twice to catch typos.
    
    Subclasses should feel free to add any additional validation they
    need, but should avoid defining a ``save()`` method -- the actual
    saving of collected user data is delegated to the active
    registration backend.

    """
    username = forms.RegexField(regex=r'^[\w.@+-]+$',
                                max_length=30,
                                label=_("Username"),
                                error_messages={'invalid': _("This value may contain only letters, numbers and @/./+/-/_ characters.")})
    
    email = forms.EmailField(label=_("E-mail"))

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['username', 'email', 'password1', 'password2']
    
    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.
        
        """
        username = self.cleaned_data['username']
        #TODO(garcianavalon) check if alfanumeric/valid for keystone

        keystone_manager = KeystoneManager()
        try:
            existing = keystone_manager.check_user(username)
            raise forms.ValidationError(_("A user with that username already exists."),
                                        code='invalid')
        except keystoneclient_exceptions.NotFound:
            return username

    def clean_email(self):
        """ Validate taht the email is not already in use"""

        email = self.cleaned_data['email']

        keystone_manager = KeystoneManager()
        try:
            existing = keystone_manager.check_email(email)
            raise forms.ValidationError(_("The email is already in use."),
                                         code='invalid')
        except keystoneclient_exceptions.NotFound:
            return email


class EmailForm(forms.Form):
    email = forms.EmailField(label=_("E-mail"))
 
class ChangePasswordForm(ConfirmPasswordForm):
    pass

        