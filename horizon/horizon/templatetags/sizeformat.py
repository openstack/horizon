# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
# Copyright 2011 Nebula, Inc.
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

"""
Template tags for displaying sizes
"""

from django import template
from django.utils import translation
from django.utils import formats


register = template.Library()


def int_format(value):
    return int(value)


def float_format(value):
    return formats.number_format(round(value, 1), 0)


def filesizeformat(bytes, filesize_number_format):
    try:
        bytes = float(bytes)
    except (TypeError, ValueError, UnicodeDecodeError):
        return translation.ungettext("%(size)d byte",
                "%(size)d bytes", 0) % {'size': 0}

    if bytes < 1024:
        return translation.ungettext("%(size)d",
                "%(size)d", bytes) % {'size': bytes}
    if bytes < 1024 * 1024:
        return translation.ugettext("%s KB") % \
                filesize_number_format(bytes / 1024)
    if bytes < 1024 * 1024 * 1024:
        return translation.ugettext("%s MB") % \
                filesize_number_format(bytes / (1024 * 1024))
    if bytes < 1024 * 1024 * 1024 * 1024:
        return translation.ugettext("%s GB") % \
                filesize_number_format(bytes / (1024 * 1024 * 1024))
    if bytes < 1024 * 1024 * 1024 * 1024 * 1024:
        return translation.ugettext("%s TB") % \
                filesize_number_format(bytes / (1024 * 1024 * 1024 * 1024))
    return translation.ugettext("%s PB") % \
            filesize_number_format(bytes / (1024 * 1024 * 1024 * 1024 * 1024))


@register.filter(name='mbformat')
def mbformat(mb):
    return filesizeformat(mb * 1024 * 1024, int_format).replace(' ', '')


@register.filter(name='diskgbformat')
def diskgbformat(gb):
    return filesizeformat(gb * 1024 * 1024 * 1024,
            float_format).replace(' ', '')
