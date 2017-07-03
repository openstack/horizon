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

from django import template

from horizon.utils import html


class Breadcrumb(html.HTMLElement):
    def __init__(self, request, template, root,
                 subfolder_path, url, attr=None):
        super(Breadcrumb, self).__init__()
        self.template = template
        self.request = request
        self.root = root
        self.subfolder_path = subfolder_path
        self.url = url
        self._subfolders = []

    def get_subfolders(self):
        if self.subfolder_path and not self._subfolders:
            (parent, slash, folder) = self.subfolder_path.strip('/') \
                .rpartition('/')
            while folder:
                path = "%s%s%s/" % (parent, slash, folder)
                self._subfolders.insert(0, (folder, path))
                (parent, slash, folder) = parent.rpartition('/')
        return self._subfolders

    def render(self):
        """Renders the table using the template from the table options."""
        breadcrumb_template = template.loader.get_template(self.template)
        extra_context = {"breadcrumb": self}
        return breadcrumb_template.render(extra_context, self.request)
