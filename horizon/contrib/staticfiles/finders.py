# Copyright 2016 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import os

from django.apps import apps
from django.contrib.staticfiles.finders import AppDirectoriesFinder


class HorizonStaticFinder(AppDirectoriesFinder):
    """Static files finder that also looks into the directory of each panel."""

    def __init__(self, app_names=None, *args, **kwargs):
        super(HorizonStaticFinder, self).__init__(*args, **kwargs)
        app_configs = apps.get_app_configs()
        for app_config in app_configs:
            if 'openstack_dashboard' in app_config.path:
                for panel in os.listdir(app_config.path):
                    panel_path = os.path.join(app_config.path, panel)
                    if os.path.isdir(panel_path) and panel != self.source_dir:

                        # Look for the static folder
                        static_path = os.path.join(panel_path, self.source_dir)
                        if os.path.isdir(static_path):
                            panel_name = app_config.name + panel
                            app_storage = self.storage_class(static_path)
                            self.storages[panel_name] = app_storage
