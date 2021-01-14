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

from horizon import tabs


class OverviewTab(tabs.Tab):
    name = _("Overview")
    slug = "overview"
    template_name = "project/images/images/_detail_overview.html"

    def get_context_data(self, request):
        image = self.tab_group.kwargs['image']
        custom_titles = settings.IMAGE_CUSTOM_PROPERTY_TITLES
        image_props = []
        for prop, val in image.properties.items():
            if prop == 'description':
                # Description property is already listed in Info section
                continue
            title = custom_titles.get(prop, prop)
            image_props.append((prop, title, val))

        return {"image": image,
                "image_props": sorted(image_props, key=lambda prop: prop[1])}


class ImageDetailTabs(tabs.TabGroup):
    slug = "image_details"
    tabs = (OverviewTab,)
