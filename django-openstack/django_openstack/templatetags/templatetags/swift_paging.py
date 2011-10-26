from django import template
from django.conf import settings
from django.utils import http

register = template.Library()


@register.inclusion_tag('django_openstack/dash/objects/_paging.html')
def object_paging(objects):
    marker = None
    if objects and not \
            len(objects) < getattr(settings, 'SWIFT_PAGINATE_LIMIT', 10000):
        last_object = objects[-1]
        marker = http.urlquote_plus(last_object.name)
    return {'marker': marker}
