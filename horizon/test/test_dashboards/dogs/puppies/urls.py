from django.conf.urls.defaults import patterns  # noqa
from django.conf.urls.defaults import url  # noqa

from horizon.test.test_dashboards.dogs.puppies.views import IndexView  # noqa

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
)
