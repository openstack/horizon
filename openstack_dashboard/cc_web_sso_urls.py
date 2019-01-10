from django.conf.urls import url
from django.conf import settings
from openstack_auth import utils
from openstack_auth import views
from openstack_dashboard import cc_websso_views
utils.patch_middleware_get_user()

cc_websso_enabled = getattr(settings, 'CC_WEBSSO_ENABLED', False)
if(cc_websso_enabled):
    urlpatterns = [
        url(r"^login/$", cc_websso_views.login, name='login'),
        url(r"^logout/$", cc_websso_views.logout, name='logout'),
        url(r'^switch/(?P<tenant_id>[^/]+)/$', views.switch,
            name='switch_tenants'),
        url(r'^switch_services_region/(?P<region_name>[^/]+)/$',
            views.switch_region,
            name='switch_services_region'),
        url(r'^switch_keystone_provider/(?P<keystone_provider>[^/]+)/$',
            views.switch_keystone_provider,
            name='switch_keystone_provider')
    ]

    if utils.is_websso_enabled():
        urlpatterns.append(url(r"^websso/$", views.websso, name='websso'))

    if utils.is_websso_enabled():
        urlpatterns.append(url(r"^ccwebsso/$", cc_websso_views.cc_websso, name='custom_websso'))
else:
    urlpatterns = []