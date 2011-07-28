from django import template
from django.dispatch import receiver
import django.dispatch

register = template.Library()

sidebar_init = django.dispatch.Signal()


@register.inclusion_tag('_sidebar_module.html')
def initiate_module_sidebar():
    response = sidebar_init.send(sender=sidebar_init)[0][1]

    return response
