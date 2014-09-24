from django.conf.urls import patterns
from django.conf.urls import url

from .views import EmailView


urlpatterns = patterns('',
    url(r'^$', EmailView.as_view(), name='index'),
)
