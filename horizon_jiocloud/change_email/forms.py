# vim: tabstop=4 shiftwidth=4 softtabstop=4

__author__      = "Vivek Dhayaal"
__copyright__   = "Copyright 2014, Reliance Jio Infocomm Ltd."

from django import shortcuts
from django.core.urlresolvers import reverse

from horizon import exceptions
from horizon import forms
from horizon import messages

from openstack_dashboard.openstack.common import timeutils

from horizon_jiocloud.common import forms as contrib_forms
from horizon_jiocloud.api import keystoneapi
from horizon_jiocloud.utils.utils import send_templated_email
from horizon_jiocloud.utils.utils import validate_ril_email

import random
import logging
LOG = logging.getLogger(__name__)


class EmailForm(contrib_forms.ContribSelfHandlingForm):
    email = forms.EmailField(widget=forms.TextInput(attrs={'placeholder': 'Your Email'}), validators=[validate_ril_email])

    def __init__(self, request, *args, **kwargs):
        super(EmailForm, self).__init__(request, *args, **kwargs)
        res = {}
        self.user = None
        try:
            res = keystoneapi.get_user(self.request.user.id)
        except Exception as ex:
            LOG.exception(ex)
            self.set_non_field_errors([self.get_default_error_message()])
            return None
        if not (res.get("success") or res.get("result")):
            return None                
        self.user = res.get("result")
        kwargs["initial"]["email"] = self.user.get("email")

    def handle(self, request, data):
        new_email = data.get("email")
        email_activation_code = "".join(map(str,
                    random.sample(range(0, 10), 5)))
        data = {"email_activation_code": email_activation_code,
                "email_activation_code_time": timeutils.strtime()}
        try:
            # email confirmation about the change
            send_templated_email("JioCloud account email change confirmation",
                [new_email],
                html_template="change_email/email_change_verification.html",
                template_context={
                "name": self.user.get("first_name") if self.user.get("first_name") else self.user.get("name"),
                "email_activation_path": reverse('horizon:settings:email:index') + 'activate/' + email_activation_code + '?email=' + new_email,
                })
            # push changes to keystone database
            response = keystoneapi.update_user(self.request.user.id, data)
            messages.success(request,
                             'Please click the link sent to your new email to activate it')
        except Exception as ex:
            LOG.exception(ex)
            response = exceptions.handle(request, ignore=True)
            messages.error(request, 'Unable to change email.')

        return shortcuts.redirect(request.build_absolute_uri())
