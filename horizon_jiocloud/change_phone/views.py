# vim: tabstop=4 shiftwidth=4 softtabstop=4

__author__      = "Vivek Dhayaal"
__copyright__   = "Copyright 2014, Reliance Jio Infocomm Ltd."

from horizon import forms
from horizon import messages

from django import shortcuts

from horizon_jiocloud.api import keystoneapi
from horizon_jiocloud.utils.utils import send_sms, OTP_SMS_MSG
from horizon_jiocloud.change_phone import forms as phone_forms

import logging
LOG = logging.getLogger(__name__)



class PhoneView(forms.ModalFormView):
    form_class = phone_forms.PhoneForm
    template_name = 'change_phone/change.html'

    def get_initial(self):
        # we use request.session as a temporary storage for the new phone 
        # number, because after the OTP is sent through SMS to user, until
        # he/she submits it through the form, we can't store the new phone
        # number in the database but still have to show it in the form
        initial = super(PhoneView, self).get_initial()
        initial["phone"] = self.request.session.get("phone")
        return initial

def sendSms(request):
     # This method serves re-sending SMS multiple times until the OTP is
     # expired, to cater to SMS sending failures.
     phone = request.session.get("phone")
     try:
         res = keystoneapi.get_user(request.user.id)
         if not (res.get("success") or res.get("result")):
             raise Exception()
     except Exception as ex:
         LOG.exception(ex)
     user = res.get("result")
     sms_activation_code = user.get("sms_activation_code")
     try:
         sms_msg = OTP_SMS_MSG + sms_activation_code
         to_num = str(phone)
         send_sms(sms_msg, to_num)
         messages.success(request,
                          'SMS sent successfully')
     except Exception as ex:
         LOG.exception(ex)
     return shortcuts.redirect('horizon:settings:phone:index')
