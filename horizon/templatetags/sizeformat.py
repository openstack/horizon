# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
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

"""
Template tags for displaying sizes
"""

from django import template
from django.utils import formats
from django.utils import translation


register = template.Library()


def int_format(value):
    return int(value)


def float_format(value):
    return formats.number_format(round(value, 1), 1)


def filesizeformat(bytes, filesize_number_format):
    try:
        bytes = float(bytes)
    except (TypeError, ValueError, UnicodeDecodeError):
        return translation.ungettext_lazy("%(size)d Byte",
                "%(size)d Bytes", 0) % {'size': 0}

    if bytes < 1024:
        bytes = int(bytes)
        return translation.ungettext_lazy("%(size)d Byte",
                "%(size)d Bytes", bytes) % {'size': bytes}
    if bytes < 1024 * 1024:
        return translation.ugettext_lazy("%s KB") % \
            filesize_number_format(bytes / 1024)
    if bytes < 1024 * 1024 * 1024:
        return translation.ugettext_lazy("%s MB") % \
            filesize_number_format(bytes / (1024 * 1024))
    if bytes < 1024 * 1024 * 1024 * 1024:
        return translation.ugettext_lazy("%s GB") % \
            filesize_number_format(bytes / (1024 * 1024 * 1024))
    if bytes < 1024 * 1024 * 1024 * 1024 * 1024:
        return translation.ugettext_lazy("%s TB") % \
            filesize_number_format(bytes / (1024 * 1024 * 1024 * 1024))
    return translation.ugettext_lazy("%s PB") % \
            filesize_number_format(bytes / (1024 * 1024 * 1024 * 1024 * 1024))


def float_cast_filesizeformat(value, multiplier=1, format=int_format):
    try:
        value = float(value)
        value = filesizeformat(value * multiplier, format).replace(' ', '')
    except (TypeError, ValueError):
        value = value or '0 bytes'
    return value


@register.filter(name='mbformat')
def mbformat(mb):
    return float_cast_filesizeformat(mb, 1024 * 1024, int_format)


@register.filter(name='mb_float_format')
def mb_float_format(mb):
    return float_cast_filesizeformat(mb, 1024 * 1024, float_format)


@register.filter(name='diskgbformat')
def diskgbformat(gb):
    return float_cast_filesizeformat(gb, 1024 * 1024 * 1024, float_format)
