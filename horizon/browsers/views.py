# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from collections import defaultdict

from horizon.tables import MultiTableView


class ResourceBrowserView(MultiTableView):
    browser_class = None
    data_method_pattern = "get_%s_data"

    def __init__(self, *args, **kwargs):
        self.browser_class = getattr(self, "browser_class", None)
        if not self.browser_class:
            raise ValueError("You must specify a ResourceBrowser class "
                             " for the browser_class attribute on %s "
                             % self.__class__.__name__)

        self.navigation_table = self.browser_class.navigation_table_class
        self.content_table = self.browser_class.content_table_class

        # Check and set up the method the view would use to collect data
        self._data_methods = defaultdict(list)
        self.table_classes = (self.navigation_table, self.content_table)
        self.get_data_methods(self.table_classes, self._data_methods)

        self._tables = {}
        self._data = {}

    def get_browser(self):
        if not hasattr(self, "browser"):
            tables = self.get_tables()
            self.browser = self.browser_class(self.request,
                                              tables,
                                              **self.kwargs)
        return self.browser

    def get_context_data(self, **kwargs):
        context = super(ResourceBrowserView, self).get_context_data(**kwargs)
        browser = self.get_browser()
        context["%s_browser" % browser.name] = browser
        return context
