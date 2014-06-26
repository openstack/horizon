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
# from cities_light.models import City
# from cities_light.models import Region
from django.core.urlresolvers import reverse  # noqa
from django.core.urlresolvers import reverse_lazy  # noqa
from django import shortcuts
from django.template import RequestContext  # noqa
from django.views.generic import TemplateView
from forms import UserSignupForm
from forms import UserSMSActivationForm
from horizon import forms
from django import shortcuts
from horizon_jiocloud.api import keystoneapi
from horizon_jiocloud.utils.utils import is_sms_expired


LOG = logging.getLogger(__name__)


class UserSignupView(forms.ModalFormView):
    form_class = UserSignupForm
    template_name = "signup/signup.html"


class UserSMSActivateView(forms.ModalFormView):
    form_class = UserSMSActivationForm
    template_name = 'signup/sms_activation.html'
    success_url = reverse_lazy('horizon_jiocloud:user_sms_activation_success')

    def get(self, *args, **kwargs):
        user = None
        res = None
        try:
            user_id = self.kwargs.get('user_id')
            res = keystoneapi.get_user(user_id)
        except Exception as ex:
            LOG.exception(str(ex))
            pass
        if res:
            if res.get("success"):
                user = res.get("result")            
        if not self.is_valid_url(user):
            return shortcuts.redirect("/")
        return super(UserSMSActivateView, self).get(*args, **kwargs)      

    def is_valid_url(self, user):
        if not user:
            return False
        if user.get("enabled"):
            return False
        if is_sms_expired(user.get("sms_activation_code_time")):
            return False
        return True

    def get_initial(self):
        return {"user_id": self.kwargs['user_id']}

    def get_context_data(self, **kwargs):
        context = super(UserSMSActivateView, self).get_context_data(**kwargs)
        context["user_id"] = self.kwargs['user_id']
        context['context_instance'] = RequestContext(self.request)
        return context


def regions(request, country_id):
    if request.is_ajax():
        regions = []
        for r in Region.objects.filter(country_id=country_id).all():
            regions.append({"name": r.name_ascii, "value": r.id})
        return shortcuts.render_to_response('common/dropdown.html',
                    {'items': regions})


def cities(request, region_id):
    if request.is_ajax():
        cities = []
        for c in City.objects.filter(region_id=region_id).all():
            cities.append({"name": c.name_ascii, "value": c.id})
        return shortcuts.render_to_response('common/dropdown.html', {'items': cities})

