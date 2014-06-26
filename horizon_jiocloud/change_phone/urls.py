# vim: tabstop=4 shiftwidth=4 softtabstop=4

__author__      = "Vivek Dhayaal"
__copyright__   = "Copyright 2014, Reliance Jio Infocomm Ltd."

from django.conf.urls import patterns  # noqa
from django.conf.urls import url  # noqa

from horizon_jiocloud.change_phone import views


urlpatterns = patterns('',
    url(r'^$', views.PhoneView.as_view(), name='index'),
    url(r'^sendSms/', views.sendSms, name='sendSms'))
