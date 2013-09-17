from django.conf.urls.defaults import patterns  # noqa
from django.conf.urls.defaults import url  # noqa

from .views import IndexView


urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
)
