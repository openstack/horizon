from django.conf.urls import url
from django.conf import settings
from openstack_auth import utils
from openstack_auth import views
from openstack_dashboard import cc_websso_views
utils.patch_middleware_get_user()

urlpatterns = [
    url(r"^login/$", cc_websso_views.login, name='login'),
    url(r"^logout/$", cc_websso_views.logout, name='logout'),
]

if utils.is_websso_enabled():
    urlpatterns.append(url(r"^ccwebsso/$", cc_websso_views.cc_websso, name='custom_websso'))