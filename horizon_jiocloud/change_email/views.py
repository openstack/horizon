# vim: tabstop=4 shiftwidth=4 softtabstop=4

__author__      = "Vivek Dhayaal"
__copyright__   = "Copyright 2014, Reliance Jio Infocomm Ltd."

from django.shortcuts import render_to_response
from horizon import forms

from horizon_jiocloud.api import keystoneapi
from horizon_jiocloud.change_email import forms as email_forms
from horizon_jiocloud.utils.utils import is_sms_expired

import logging
LOG = logging.getLogger(__name__)



class EmailView(forms.ModalFormView):
    form_class = email_forms.EmailForm
    template_name = 'change_email/change.html'

    def get_initial(self):
        initial = super(EmailView, self).get_initial()
        initial["email"] = ''
        return initial

def activate(request, activation_code):
     new_email = request.GET.get('email', '')
     try:
         res = keystoneapi.get_user(request.user.id)
         if not (res.get("success") or res.get("result")):
             raise Exception()
     except Exception as ex:
         LOG.exception(ex)
         return render_to_response('change_email/email_change_failure.html')
     user = res.get("result")
     email_activation_code = user.get("email_activation_code")
     email_activation_code_time = user.get("email_activation_code_time")
     if not new_email or email_activation_code != activation_code or is_sms_expired(email_activation_code_time):
         return render_to_response('change_email/email_change_failure.html')
     # codes matched. so we will change the email in database
     try:
         # push changes to keystone database
         if user.get("name") == user.get("email"):
             response = keystoneapi.update_user(request.user.id, {"name" : new_email, "email" : new_email})
         else:
             response = keystoneapi.update_user(request.user.id, {"email" : new_email})
     except Exception as ex:
         LOG.exception(ex)
         return render_to_response('change_email/email_change_failure.html')
     return render_to_response('change_email/email_change_success.html')
