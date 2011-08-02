from django import template
from django_openstack import signals

register = template.Library()



@register.inclusion_tag('_sidebar_module.html')
def initiate_module_sidebar():
    return {'modules': [module[1] for module in signals.dash_apps_detection()] }
