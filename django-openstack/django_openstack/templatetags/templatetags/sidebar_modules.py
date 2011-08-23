from django import template
from django_openstack import signals

register = template.Library()


@register.inclusion_tag('_sidebar_module.html')
def dash_sidebar_modules(request):
    if signals.dash_apps_detect()[0][1]['type'] == "dash":
        return {'modules': [module[1] for module in signals.dash_apps_detect()],
                'request': request }

@register.inclusion_tag('_sidebar_module.html')
def syspanel_sidebar_modules(request):
    if signals.dash_apps_detect()[0][1]['type'] == "syspanel":
        return {'modules': [module[1] for module in signals.dash_apps_detect()],
                'request': request }

