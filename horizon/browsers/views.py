# Copyright 2012 Nebula, Inc.
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

from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.views import generic

import horizon
from horizon.tables import MultiTableView
from horizon.utils import memoized


class ResourceBrowserView(MultiTableView):
    browser_class = None

    def __init__(self, *args, **kwargs):
        if not self.browser_class:
            raise ValueError("You must specify a ResourceBrowser subclass "
                             "for the browser_class attribute on %s."
                             % self.__class__.__name__)
        self.table_classes = (self.browser_class.navigation_table_class,
                              self.browser_class.content_table_class)
        self.navigation_selection = False
        super(ResourceBrowserView, self).__init__(*args, **kwargs)

    @memoized.memoized_method
    def get_browser(self):
        browser = self.browser_class(self.request, **self.kwargs)
        browser.set_tables(self.get_tables())
        if not self.navigation_selection:
            ct = browser.content_table
            item = browser.navigable_item_name.lower()
            ct._no_data_message = _("Select a %s to browse.") % item
        return browser

    def get_tables(self):
        tables = super(ResourceBrowserView, self).get_tables()
        # Tells the navigation table what is selected.
        navigation_table = tables[
            self.browser_class.navigation_table_class._meta.name]
        navigation_item = self.kwargs.get(
            self.browser_class.navigation_kwarg_name)
        navigation_table.current_item_id = navigation_item
        return tables

    def get_context_data(self, **kwargs):
        context = super(ResourceBrowserView, self).get_context_data(**kwargs)
        browser = self.get_browser()
        context["%s_browser" % browser.name] = browser
        return context


class AngularIndexView(generic.TemplateView):
    '''View for Angularized panel

    title: to display title for browser window or tab.
    page_title: to display current position in breadcrumb.

    Sample usage is as follows.
    from horizon.browsers import views
    views.AngularIndexView.as_view(title="Images")
    views.AngularIndexView.as_view(title="Browser Title",
                                   page_title="Page Title")
    '''
    template_name = 'angular.html'
    title = _("Horizon")
    page_title = None

    def get_context_data(self, **kwargs):
        context = super(AngularIndexView, self).get_context_data(**kwargs)
        context["title"] = self.title
        context["csrf_http"] = settings.CSRF_COOKIE_HTTPONLY
        if self.page_title is None:
            context["page_title"] = self.title
        else:
            context["page_title"] = self.page_title
        return context


class AngularDetailsView(generic.TemplateView):
    '''View for Angularized details view

    This is used to load ngdetails view via Django.
    i.e. refresh or link directly for '^ngdetails/'
    '''
    template_name = 'angular.html'

    def get_context_data(self, **kwargs):
        context = super(AngularDetailsView, self).get_context_data(**kwargs)
        # some parameters are needed for navigation side bar and breadcrumb.
        title = _("Horizon")
        context["title"] = title
        context["page_title"] = title
        context["csrf_http"] = settings.CSRF_COOKIE_HTTPONLY
        # set default dashboard and panel
        dashboard = horizon.get_default_dashboard()
        self.request.horizon['dashboard'] = dashboard
        self.request.horizon['panel'] = dashboard.get_panels()[0]
        # set flag that means routed by django
        context['routed_by_django'] = True
        return context
