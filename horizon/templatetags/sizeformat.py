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

from oslo_utils import units

from django import template
from django.utils import formats
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext_lazy


register = template.Library()


def int_format(value):
    return int(value)


def float_format(value):
    rounded_value = round(value, 1)
    if rounded_value.is_integer():
        decimal_pos = 0
    else:
        decimal_pos = 1
    return formats.number_format(rounded_value, decimal_pos)


def filesizeformat(bytes, filesize_number_format):
    try:
        bytes = float(bytes)
    except (TypeError, ValueError, UnicodeDecodeError):
        return ungettext_lazy("%(size)d Byte",
                              "%(size)d Bytes", 0) % {'size': 0}

    if bytes < units.Ki:
        bytes = int(bytes)
        return ungettext_lazy("%(size)d Byte",
                              "%(size)d Bytes", bytes) % {'size': bytes}
    if bytes < units.Mi:
        return _("%s KB") % filesize_number_format(bytes / units.Ki)
    if bytes < units.Gi:
        return _("%s MB") % filesize_number_format(bytes / units.Mi)
    if bytes < units.Ti:
        return _("%s GB") % filesize_number_format(bytes / units.Gi)
    if bytes < units.Pi:
        return _("%s TB") % filesize_number_format(bytes / units.Ti)
    return _("%s PB") % filesize_number_format(bytes / units.Pi)


def float_cast_filesizeformat(value, multiplier=1, format=int_format):
    try:
        value = float(value)
        value = filesizeformat(value * multiplier, format).replace(' ', '')
    except (TypeError, ValueError):
        value = value or _('0 Bytes')
    return value


@register.filter(name='mbformat')
def mbformat(mb):
    return float_cast_filesizeformat(mb, units.Mi, int_format)


@register.filter(name='mb_float_format')
def mb_float_format(mb):
    return float_cast_filesizeformat(mb, units.Mi, float_format)


@register.filter(name='diskgbformat')
def diskgbformat(gb):
    return float_cast_filesizeformat(gb, units.Gi, float_format)
