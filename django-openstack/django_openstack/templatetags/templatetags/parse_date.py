"""
Template tags for parsing date strings.
"""

import datetime
from django import template

register = template.Library()

def _parse_datetime(dtstr):
    try:
        return datetime.datetime.strptime(dtstr, "%Y-%m-%dT%H:%M:%S.%f")
    except:
        try:
            return datetime.datetime.strptime(dtstr, "%Y-%m-%d %H:%M:%S.%f")
        except:
            return datetime.datetime.strptime(dtstr, "%Y-%m-%d %H:%M:%S")


class ParseDateNode(template.Node):
    def render(self, context):
        """Turn an iso formatted time back into a datetime."""
        if context == None:
            return "None"
        date_obj = _parse_datetime(context)
        return date_obj.strftime("%m/%d/%y at %H:%M:%S")


@register.filter(name='parse_date')
def parse_date(value):
    return ParseDateNode().render(value)


@register.filter(name='parse_datetime')
def parse_datetime(value):
    return _parse_datetime(value)


@register.filter(name='pretty_date')
def pretty_date(value):
    return value.strftime("%d/%m/%y at %H:%M:%S")
