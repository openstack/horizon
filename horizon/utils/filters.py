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

import datetime

import iso8601

from django.template.defaultfilters import register
from django.template.defaultfilters import timesince
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


@register.filter
def replace_underscores(string):
    return string.replace("_", " ")


@register.filter
def parse_isotime(timestr, default=None):
    # This duplicates oslo timeutils parse_isotime but with a
    # @register.filter annotation and a silent fallback on error.
    try:
        return iso8601.parse_date(timestr)
    except (iso8601.ParseError, TypeError):
        return default or ''


@register.filter
def timesince_or_never(dt, default=None):
    """Call the Django ``timesince`` filter or a given default string.

    It returns the string *default* if *dt* is not a valid ``date``
    or ``datetime`` object.
    When *default* is None, "Never" is returned.
    """
    if default is None:
        default = _("Never")

    if isinstance(dt, datetime.date):
        return timesince(dt)
    else:
        return default


@register.filter
def timesince_sortable(dt):
    delta = timezone.now() - dt
    # timedelta.total_seconds() not supported on python < 2.7
    seconds = delta.seconds + (delta.days * 24 * 3600)
    return mark_safe("<span data-seconds=\"%d\">%s</span>" %
                     (seconds, timesince(dt)))
