from django.conf.urls.defaults import patterns, url

from .views import IndexView, DetailView, CreateVolumeTypeView

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^create_type$', CreateVolumeTypeView.as_view(), name='create_type'),
    url(r'^(?P<volume_id>[^/]+)/$', DetailView.as_view(), name='detail'),
)
