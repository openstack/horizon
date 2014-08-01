from django.conf.urls import patterns  # noqa
from django.conf.urls import url  # noqa

from horizon.test.test_dashboards.dogs.puppies.views import IndexView  # noqa
from horizon.test.test_dashboards.dogs.puppies.views import TwoTabsView  # noqa

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^tabs/$', TwoTabsView.as_view(), name='tabs'),
)
