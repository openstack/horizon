# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Reliance Jio Infocomm, Ltd.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import logging

from captcha.fields import ReCaptchaField
# from cities_light.models import City
# from cities_light.models import Region
# from cities_light.models import Country
from horizon_jiocloud.api import keystoneapi
from horizon_jiocloud.common import forms as contrib_forms
from horizon_jiocloud.utils.utils import send_sms
from horizon_jiocloud.utils.utils import send_templated_email
from horizon_jiocloud.utils.utils import is_sms_expired
from horizon_jiocloud.utils.utils import validate_ril_email
from django.core.urlresolvers import reverse_lazy  # noqa
from django import http
from django.utils.translation import ugettext_lazy as _  # noqa
from django.views.decorators.debug import sensitive_variables  # noqa
from horizon import forms
from horizon.utils import validators
from keystoneclient import exceptions as keystoneclient_exceptions
from openstack_dashboard.openstack.common import timeutils
import random
from django.conf import settings
from django.shortcuts import render_to_response

try:
    import simplejson as json
except ImportError:
    import json

LOG = logging.getLogger(__name__)

class UserSignupForm(contrib_forms.ContribSelfHandlingForm):
    first_name = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Name'}))
    # last_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Your Email'}), validators=[validate_ril_email])
    # confirm_email = forms.EmailField()

    password = forms.RegexField(
        label=_("Password"),
        widget=forms.PasswordInput(render_value=False, attrs={'placeholder': 'New Password'}),
        regex=validators.password_validator(),
        error_messages={'invalid': validators.password_validator_msg()})
    # confirm_password = forms.CharField(
    #     label=_("Confirm Password"),
    #     required=False,
    #     widget=forms.PasswordInput(render_value=False))

    # company = forms.CharField()
    # address = forms.CharField()
    # country = forms.ChoiceField(label=_("Country"), required=True)
    # state = forms.ChoiceField(label=_("State"), required=True)
    # city = forms.ChoiceField(label=_("City"), required=True)
    # pincode = forms.CharField()
    # country_code = forms.CharField()
    phone = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Your Phone Number'}))
    captcha = ReCaptchaField()
    # terms = forms.BooleanField(
    #     error_messages={
    #         'required': 'You must accept the terms and conditions'},
    #     label="Terms &amp; Conditions"
    # )

    def __init__(self, request, *args, **kwargs):
        super(UserSignupForm, self).__init__(request, *args, **kwargs)
        # self.fields["country"].choices = [(c.id, c.name_ascii) for c in Country.objects.all()]
        # if request.method == "GET":
        #     default_country = self.get_default_country()
        #     if default_country:
        #         self.fields["country"].initial = default_country.id
        #         self.fields["state"].choices = [(s.id, s.name_ascii) for s in Region.objects.filter(country_id=default_country.id).all()]
        #         default_state= self.get_default_state()
        #         if default_state:
        #             self.fields["state"].initial = default_state.id
        #             self.fields["city"].choices = [(ci.id, ci.name_ascii) for ci in City.objects.filter(region_id=default_state.id).all()]
        #             default_city= self.get_default_city()
        #             if default_city:
        #                 self.fields["city"].initial = default_city.id
        # elif request.method == "POST":
        #     country_id = request.POST.get("country")
        #     if country_id:
        #         self.fields["country"].initial = country_id
        #         self.fields["state"].choices = [(s.id, s.name_ascii) for s in Region.objects.filter(country_id=country_id).all()]
        #         state_id = request.POST.get("state")
        #         if state_id:
        #             self.fields["state"].initial = state_id
        #             self.fields["city"].choices = [(ci.id, ci.name_ascii) for ci in City.objects.filter(region_id=state_id).all()]
        #             city_id = request.POST.get("city")
        #             if city_id:
        #                 self.fields["city"].initial = city_id

    def get_default_country(self):
        country = self.get_country(name="India")
        if country:
            return  country[0]

    def get_default_state(self):
        state = self.get_state(name="Maharashtra")
        if state:
            return  state[0]

    def get_default_city(self):
        city = self.get_city(name="Mumbai")
        if city:
            return  city[0]          

    def get_country(self, id=None, name=None):
        """
        """
        qry = Country.objects
        if id:
            qry = qry.filter(id=id)
        if name:
            qry = qry.filter(name=name)
        return qry.all()

    def get_state(self, id=None, name=None):
        """
        """
        qry = Region.objects
        if id:
            qry = qry.filter(id=id)
        if name:
            qry = qry.filter(name=name)
        return qry.all()

    def get_city(self, id=None, name=None):
        """
        """
        qry = City.objects
        if id:
            qry = qry.filter(id=id)
        if name:
            qry = qry.filter(name=name)
        return qry.all()

    def clean(self):
        '''Check to make sure password fields match.'''
        data = super(forms.Form, self).clean()
        # if 'password' in data:
        #     if data['password'] != data.get('confirm_password', None):
        #         raise ValidationError(_('Passwords do not match.'))
        # if 'email' in data:
        #     if data['email'] != data.get('confirm_email', None):
        #         raise ValidationError(_('Emails do not match.'))
        return data

    @sensitive_variables('data')
    def handle(self, request, data):
        res = {}
        user_id = None
        password = data.get("password")
        email = data.get("email")
        first_name = data.get("first_name")
        # last_name = data.get("last_name")
        # company = data.get("company")
        # address = data.get("address")
        # country_code = data.get("country_code")
        # country = data.get("country")
        # country_list = self.get_country(country)
        # if country_list:
        #     country_name = country_list[0].name_ascii
        # state = data.get("state")
        # state_list = self.get_state(state)
        # if state_list:
        #     state_name = state_list[0].name_ascii
        # city = data.get("city")
        # city_list = self.get_city(city)
        # if city_list:
        #     city_name = city_list[0].name_ascii
        # pin = data.get("pincode")
        phone = data.get("phone")
        sms_activation_code = "".join(map(str,
                    random.sample(range(0, 10), 5)))
        _data = {"password": password, "email": email,
            "first_name": first_name, 
            # "last_name": last_name,
            # "country": country, "address": address, "city": city,
            # "state": state, "pin": pin, "company": company, 
            # "country_code": country_code,
             "phone": phone, "sms_activation_code": sms_activation_code,
            "sms_activation_code_time": timeutils.strtime()}

        try:
            res = keystoneapi.create_user(_data)
        except Exception as ex:
            LOG.exception(ex)
            self.set_non_field_errors([self.get_default_error_message()])
            return None
        if not res.get("success"):
            self.set_non_field_errors([
                    res.get("error",
                            self.get_default_error_message()
                        )
                ])
            return None
        else:
            user = res["result"]
            user_id = user.get("id")
            try:
                send_templated_email("JioCloud account activation",
                    [user.get("email")],
                    html_template="signup/account_activation_email.html",
                    template_context={
                        "user_id": user_id,
                        "name": user.get("name"),
                        "SITE_URL": getattr(settings, "SITE_URL", "http://127.0.0.1"),
                    })
            except Exception as ex:
                LOG.exception(ex)
            try:
                sms_msg = getattr(settings, "SMS_SYSTEM_MSG", "") + sms_activation_code
                #Convert to str: Fix:UnicodeDecodeError: 'ascii' codec can't decode byte 0x84 in position 0: ordinal not in range(128)
                to_num = str(phone)
                send_sms(sms_msg, to_num)
            except Exception as ex:
                ##TODO(SM):Delete user from keystone ?
                LOG.exception(ex)
                self.set_non_field_errors([
                        self.get_default_error_message()
                    ])
                return None

            # return http.HttpResponseRedirect(
            #     reverse_lazy(
            #         'user_sms_activation',
            #         kwargs={"user_id": user_id}
            #     ))
            return render_to_response('signup/signup_success.html', 
                    {'email':settings.DEFAULT_FROM_EMAIL})


class UserSMSActivationForm(contrib_forms.ContribSelfHandlingForm):
    code = forms.CharField(required=True, max_length=5, min_length=5,
                help_text=_("Please enter the activation code"),
                widget=forms.TextInput(attrs={'placeholder': 'Your Activation Code'}))
    user_id = forms.CharField(widget=forms.HiddenInput, required=False)

    @sensitive_variables('data')
    def handle(self, request, data):
        res = {}
        user = None
        try:
            code = data.get("code")
            user_id = data.get("user_id")
            try:
                res = keystoneapi.get_user(user_id)
            except Exception as ex:
                LOG.exception(ex)
                self.set_non_field_errors([self.get_default_error_message()])
                return None

            if not res.get("success"):
                self.set_non_field_errors(["Invalid Account"])
                return None                
            user = res.get("result")
            if not user:
                self.set_non_field_errors(["Invalid Account"])
                return None
            else:
                if user.get("enabled"):
                    self.set_non_field_errors(["Account already activated"])
                    return None
                else:
                    sms_activation_code = user.get("sms_activation_code")
                    sms_activation_code_time = \
                            user.get("sms_activation_code_time")
                    if not (sms_activation_code and sms_activation_code_time):
                        self.set_non_field_errors(["Invalid Activation Code"])
                        return None
                    if sms_activation_code not in [code]:
                        self.set_non_field_errors(["Invalid Activation Code"])
                        return None
                    if is_sms_expired(sms_activation_code_time):
                        self.set_non_field_errors(["Account Activation Code Expired"])
                        return None
                    user_id = user.get("id")
                    if not user_id:
                        self.set_non_field_errors(["Invalid Account"])
                        return None
                    _data = {"user_id": user_id}
                    try:
                        res = keystoneapi.activate_user(_data)
                        keystoneapi.update_user(user_id, {"sms_activation_code" : ""})
                    except Exception as ex:
                        LOG.exception(ex)
                        self.set_non_field_errors([self.get_default_error_message()])
                        return None
                    try:
                        send_templated_email("JioCloud account activated",
                            [user.get("email")],
                            html_template="signup/registration_success_email.html",
                            template_context={
                            "name": user.get("name"),
                            "SITE_URL": getattr(settings, "SITE_URL", "http://127.0.0.1"),
                            })
                    except Exception as ex:
                        LOG.exception(ex)
        except Exception as ex:
            import traceback
            traceback.print_exc()
            LOG.exception(ex)
            self.set_non_field_errors([self.get_default_error_message()])
            return None
        if not res.get("success"):
            self.set_non_field_errors([
                    res.get("error", 
                            self.get_default_error_message()
                        )
                ])
            return None
        return res
