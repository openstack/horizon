from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

from horizon.test.test_dashboards.cats.kittens.views import IndexView

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
)
