from django.conf.urls.defaults import patterns  # noqa
from django.conf.urls.defaults import url  # noqa

from horizon.test.test_dashboards.cats.kittens.views import IndexView  # noqa

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
)
