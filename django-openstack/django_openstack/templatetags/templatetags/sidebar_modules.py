from django import template
from django_openstack import signals

register = template.Library()


@register.inclusion_tag('_sidebar_module.html')
def dash_sidebar_modules(request):
    signals_call = signals.dash_modules_detect()
    if signals_call:
        if signals_call[0][1]['type'] == "dash":
            return {'modules': [module[1] for module in signals_call],
                    'request': request }
    else:
        return {}
        
@register.inclusion_tag('_sidebar_module.html')
def syspanel_sidebar_modules(request):
    signals_call = signals.dash_modules_detect()
    if signals_call:
        if signals_call[0][1]['type'] == "syspanel":
            return {'modules': [module[1] for module in signals_call],
                    'request': request }
    else:
        return {}
