"""
Template tags for displaying sizes
"""

import datetime
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
    except (TypeError,ValueError,UnicodeDecodeError):
        return translation.ungettext("%(size)d byte", "%(size)d bytes", 0) % {'size': 0}

    if bytes < 1024:
        return translation.ungettext("%(size)d", "%(size)d", bytes) % {'size': bytes}
    if bytes < 1024 * 1024:
        return translation.ugettext("%s KB") % filesize_number_format(bytes / 1024)
    if bytes < 1024 * 1024 * 1024:
        return translation.ugettext("%s MB") % filesize_number_format(bytes / (1024 * 1024))
    if bytes < 1024 * 1024 * 1024 * 1024:
        return translation.ugettext("%s GB") % filesize_number_format(bytes / (1024 * 1024 * 1024))
    if bytes < 1024 * 1024 * 1024 * 1024 * 1024:
        return translation.ugettext("%s TB") % filesize_number_format(bytes / (1024 * 1024 * 1024 * 1024))
    return translation.ugettext("%s PB") % filesize_number_format(bytes / (1024 * 1024 * 1024 * 1024 * 1024))


@register.filter(name='mbformat')
def mbformat(mb):
    return filesizeformat(mb * 1024 * 1024, int_format).replace(' ', '')


@register.filter(name='diskgbformat')
def diskgbformat(gb):
    return filesizeformat(gb * 1024 * 1024 * 1024, float_format).replace(' ', '')
