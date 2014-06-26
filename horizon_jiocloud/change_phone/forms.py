# vim: tabstop=4 shiftwidth=4 softtabstop=4

__author__      = "Vivek Dhayaal"
__copyright__   = "Copyright 2014, Reliance Jio Infocomm Ltd."

from django import shortcuts

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.openstack.common import timeutils

from horizon_jiocloud.common import forms as contrib_forms
from horizon_jiocloud.api import keystoneapi
from horizon_jiocloud.utils.utils import send_sms, OTP_SMS_MSG
from horizon_jiocloud.utils.utils import send_templated_email
from horizon_jiocloud.utils.utils import is_sms_expired

import random
import logging
LOG = logging.getLogger(__name__)


class PhoneForm(contrib_forms.ContribSelfHandlingForm):
    phone = forms.CharField(max_length=10, min_length=10,
                widget=forms.TextInput(attrs={'placeholder': 'Enter Your Phone Number'}))
    sms_activation_code = forms.CharField(max_length=5, min_length=5,
                label="Please enter the SMS code sent to your mobile number",
                widget=forms.TextInput(attrs={'placeholder': 'Your Activation Code'}))

    def __init__(self, request, *args, **kwargs):
        super(PhoneForm, self).__init__(request, *args, **kwargs)
        res = {}
        self.user = None
        self.sms_expired = True
        request.session["show_sms_button"] = None
        try:
            # erro handling: when the user details could not be fetched,
            # show the default error message
            try:
                res = keystoneapi.get_user(self.request.user.id)
            except Exception as ex:
                LOG.exception(ex)
                self.set_non_field_errors([self.get_default_error_message()])
                del self.fields["sms_activation_code"]
                return None
            if not (res.get("success") or res.get("result")):
                del self.fields["sms_activation_code"]
                return None                
            self.user = res.get("result")
            if not kwargs["initial"]["phone"]:
                # we populate the initial value from request.session in views.py
                # No intial value implies that the user hasn't yet started the 
                # phone number change process and hasn't keyed-in the new phone
                # number. So, pre-fill the field with the current phone number
                # from database
                kwargs["initial"]["phone"] = self.user.get("phone")
            sms_activation_code = self.user.get("sms_activation_code")
            sms_activation_code_time = \
                    self.user.get("sms_activation_code_time")
            self.sms_expired = is_sms_expired(sms_activation_code_time)
            if (not (sms_activation_code and sms_activation_code_time)) or \
               self.sms_expired:
                # empty sms_activation_code => the user hasn't yet started the
                # phone number change process.
                # sms_expired => the user has to generate a new OTP.
                # In either case, remove the sms_activation_code field from form
                del self.fields["sms_activation_code"]
                return None
            else:
                # the user is in the middle of phone number change.
                # In some cases, SMS may not have been delivered.
                # So, set this flag to true. Based on this flag, 'Resend SMS'
                # button will be displayed in UI. Logic to this effect is 
                # implemented in the template
                request.session["show_sms_button"] = True
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

    def handle(self, request, data):
        phone = data.get("phone")
        request.session["phone"] = phone
        if not self.fields.has_key("sms_activation_code"):
            # No "sms_activation_code" field in form
            # So generate OTP to start phone number change process;
            # send SMS containing the OTP and store OTP details
            # in database for later verification
            sms_activation_code = "".join(map(str,
                        random.sample(range(0, 10), 5)))
            data = {"sms_activation_code": sms_activation_code,
                    "sms_activation_code_time": timeutils.strtime()}
            try:
                sms_msg = OTP_SMS_MSG + sms_activation_code
                to_num = str(phone)
                send_sms(sms_msg, to_num)
                messages.success(request,
                                 'Please enter the SMS code to change phone number')
            except Exception as ex:
                LOG.exception(ex)
                self.set_non_field_errors([
                        self.get_default_error_message()
                    ])
                return None
        else:
            # check if the code submitted in the form and that in the 
            # database match
            code = data.get("sms_activation_code")
            sms_activation_code = self.user.get("sms_activation_code")
            if sms_activation_code not in [code]:
                self.set_non_field_errors(["Invalid Activation Code"])
                return None
            # codes matched. so we will change the phone number
            # in database.
            # sms_activation_code no more required so unset it
            # in database.
            data["sms_activation_code"] = ""
            request.session["phone"] = ""
            try:
                # email confirmation about the change
                send_templated_email("JioCloud account phone number changed",
                    [self.user.get("email")],
                    html_template="change_phone/phone_change_cofirmation_email.html",
                    template_context={
                    "name": self.user.get("first_name") if self.user.get("first_name") else self.user.get("name"),
                    "phone": phone,
                    })
                messages.success(request,
                                 'Phone number has been updated successfully.')
            except Exception as ex:
                LOG.exception(ex)

        try:
            # push changes to keystone database
            response = keystoneapi.update_user(self.request.user.id, data)
        except Exception:
            response = exceptions.handle(request, ignore=True)
            messages.error(request, 'Unable to change phone number.')

        return shortcuts.redirect(request.build_absolute_uri())
