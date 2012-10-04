from django.conf.urls.defaults import patterns, url

from .views import IndexView, DetailView

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^(?P<volume_id>[^/]+)/$', DetailView.as_view(), name='detail'),
)
