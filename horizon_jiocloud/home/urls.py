# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2013 Reliance Jio Infocomm, Ltd.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.conf.urls import patterns  # noqa
from django.conf.urls import url  # noqa
import views
from django.contrib.auth.decorators import login_required

urlpatterns = patterns('',
    #url(r'^$', login_required(views.HomeView.as_view()), name='home'),
    url(r'^$', login_required(views.HomeView), name='home'),
    ##to override the default horizone home url
    ##defined in the horizon/horizon/site_urls.py
    #url(r'^home/$', login_required(views.HomeView.as_view()), name='user_home'),
    url(r'^home/$', login_required(views.HomeView), name='user_home'),
    url(r'^page-under-construction$', login_required(views.PageUnderConstructionView.as_view()), name='page_under_construction'),
    url(r'^api-documentation', login_required(views.ApiDocumentation.as_view()), name='api_documentation'),
    url(r'^compute', login_required(views.ComputeView.as_view()), name='compute'),
    url(r'^object-store', login_required(views.ObjectStoreView.as_view()), name='object-store'),
    url(r'^block-store', login_required(views.BlockStoreView.as_view()), name='block-store'),
    url(r'^starter-guide', login_required(views.StarterGuideView.as_view()), name='starter-guide'),
    url(r'^faqs', login_required(views.FaqsView.as_view()), name='faqs'),
    url(r'features', login_required(views.FeaturesView.as_view()), name='features'),
    url(r'documentation', login_required(views.DocumentationView.as_view()), name='documentation')


)

