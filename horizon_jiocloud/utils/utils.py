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

from django.conf import settings  # noqa
from django.core.mail import EmailMultiAlternatives  # noqa
from django.template import Context  # noqa
from django.template.loader import get_template  # noqa
from django.forms import ValidationError  # noqa
import logging
from openstack_dashboard.openstack.common.gettextutils import _
import smpplib
from openstack_dashboard.openstack.common import timeutils

LOG = logging.getLogger(__name__)
OTP_SMS_MSG="Kindly enter the following code on your screen "


def send_sms(body, to):
    sms_system_hostname = getattr(settings, 'SMS_SYSTEM_HOSTNAME', None)
    sms_system_port = getattr(settings, 'SMS_SYSTEM_PORT', None)
    sms_system_id = getattr(settings, 'SMS_SYSTEM_ID', None)
    sms_system_password = getattr(settings, 'SMS_SYSTEM_PASSWORD', None)
    from_ = getattr(settings, 'SMS_SYSTEM_SOURCE_ADDR', None)
    client = None
    try:
            client = smpplib.client.Client(sms_system_hostname,
                                        sms_system_port)
            client.connect()
            try:
                    client.bind_transmitter(system_id=sms_system_id,
                                        password=sms_system_password)

                    client.send_message(
                        source_addr_ton=smpplib.consts.SMPP_TON_INTL,
                        source_addr=from_,
                        dest_addr_ton=smpplib.consts.SMPP_TON_INTL,
                        destination_addr=to,
                        short_message=body)
            finally:
                    LOG.info(_('destination phone:%(to)s,\
                        client.state:%(state)s'),
                        {'state': client.state, 'to': to})
                    if client.state in [
                        smpplib.consts.SMPP_CLIENT_STATE_BOUND_TX
                    ]:
                            #if bound to transmitter
                            try:
                                    client.unbind()
                            except smpplib.exceptions.UnknownCommandError:
                                    """Known issue:
                                        https://github.com/
                                        podshumok/python-smpplib/issues/2
                                    """
                                    try:
                                            client.unbind()
                                    except smpplib.exceptions.PDUError:
                                            pass
    finally:
            if client:
                    LOG.info(_('destination phone:%(to)s, \
                        client.state:%(state)s'),
                    {'state': client.state, 'to': to})
                    client.disconnect()
                    LOG.info(_('destination phone:%(to)s, \
                        client.state:%(state)s'),
                    {'state': client.state, 'to': to})


def send_templated_email(subject, to_emails, plain_text_template=None,
            from_email=None, html_template=None, template_context=None):
    html_content = None
    text_content = None
    if not template_context:
        template_context = {}
    ctx = Context(template_context)
    if html_template:
        html_content = get_template(html_template).render(ctx)
    if plain_text_template:
        text_content = get_template(plain_text_template).render(ctx)
    msg = EmailMultiAlternatives(subject, text_content, from_email, to_emails)
    if html_content:
        msg.attach_alternative(html_content, "text/html")
    msg.send()


def is_sms_expired(sms_activation_code_time):
    if sms_activation_code_time:
        current_time = timeutils.utcnow()
        time_diff = current_time - \
            timeutils.parse_strtime(sms_activation_code_time)
        #5 minutes
        sms_timeout = getattr(settings, "SMS_SYSTEM_SMS_TIMEOUT", 300)
        if time_diff.seconds > sms_timeout:
            return True
        else:
            return False      
    return True  

def get_registration_service_endpoint():
    endpoint = getattr(settings, "REGISTRATION_SERVICE_ENDPOINT", "http://127.0.0.1")
    return endpoint

def validate_ril_email(value):
    if value[-8:] != "@ril.com":
        raise ValidationError(u'%s is not a valid email' % value)
