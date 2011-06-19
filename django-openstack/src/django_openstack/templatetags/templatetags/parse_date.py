"""
Template tags for parsing date strings.
"""

import datetime
from django import template

register = template.Library()

class ParseDateNode(template.Node):
    def render(self, context):
        """Turn an iso formatted time back into a datetime."""
        if context == None:
            return "None"
        else:
            try:
                date_obj = datetime.datetime.strptime(context, "%Y-%m-%dT%H:%M:%S.%f")
            except:
                date_obj = datetime.datetime.strptime(context, "%Y-%m-%d %H:%M:%S.%f")
        return date_obj.strftime("%d/%m/%y at %H:%M:%S")


@register.filter(name='parse_date')
def parse_date(value):
    return ParseDateNode().render(value)
