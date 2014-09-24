from django.conf.urls import patterns
from django.conf.urls import url

from .views import CancelView


urlpatterns = patterns('',
    url(r'^$', CancelView.as_view(), name='index'),
)
