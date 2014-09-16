from django.conf.urls import patterns
from django.conf.urls import url

from horizon.test.test_dashboards.cats.kittens.views import IndexView  # noqa

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
)
