from django.conf.urls import patterns  # noqa
from django.conf.urls import url  # noqa

from horizon.test.test_dashboards.cats.tigers.views import IndexView  # noqa

urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='index'),
)
