# vim: tabstop=4 shiftwidth=4 softtabstop=4

from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('django_openstack.dash.views.instances',
  url(r'^(?P<tenant_id>[^/]+)/instances', 'index', name='dash_instances'),
)

urlpatterns += patterns('django_openstack.dash.views.images',
  url(r'^(?P<tenant_id>[^/]+)/images/$', 'index', name='dash_images'),
  url(r'^(?P<tenant_id>[^/]+)/images/upload/$',
      'upload',
      name='dash_images_upload'),
  url(r'^(?P<tenant_id>[^/]+)/images/(?P<image_id>[^/]+)/launch/$',
      'launch',
      name='dash_images_launch'),
)
