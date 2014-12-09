from django.conf.urls import patterns
from django.conf.urls import url

from .views import MultiFormView


urlpatterns = patterns('',
    url(r'^$', MultiFormView.as_view(), name='index'),
)
