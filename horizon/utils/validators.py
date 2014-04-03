# Copyright 2012 Nebula, Inc.
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

import re

from django.core.exceptions import ValidationError  # noqa
from django.core import validators  # noqa
from django.utils.translation import ugettext_lazy as _

from horizon import conf


def validate_port_range(port):
    if port not in range(-1, 65536):
        raise ValidationError(_("Not a valid port number"))


def validate_ip_protocol(ip_proto):
    if ip_proto not in range(-1, 256):
        raise ValidationError(_("Not a valid IP protocol number"))


def password_validator():
    return conf.HORIZON_CONFIG["password_validator"]["regex"]


def password_validator_msg():
    return conf.HORIZON_CONFIG["password_validator"]["help_text"]


def validate_port_or_colon_separated_port_range(port_range):
    """Accepts a port number or a single-colon separated range."""
    if port_range.count(':') > 1:
        raise ValidationError(_("One colon allowed in port range"))
    ports = port_range.split(':')
    for port in ports:
        try:
            if int(port) not in range(-1, 65536):
                raise ValidationError(_("Not a valid port number"))
        except ValueError:
            raise ValidationError(_("Port number must be integer"))

# Same as POSIX [:print:]. Accordingly, diacritics are disallowed.
PRINT_REGEX = re.compile(r'^[\x20-\x7E]*$')

validate_printable_ascii = validators.RegexValidator(
    PRINT_REGEX,
    _("The string may only contain ASCII printable characters."),
    "invalid_characters")
