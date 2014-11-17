# Copyright (C) 2014 Universidad Politecnica de Madrid
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from horizon.tables import actions as horizon_actions

class InlineCreateAction(horizon_actions.BaseAction):
    """Custom action to enable inline creation of elements through AJAX.

    It's inspired by the filter action and the update action.
    """

    ajax = True
    def __init__(self, **kwargs):
        super(InlineCreateAction, self).__init__()
        self.method = kwargs.get('method', "POST")
        self.name = kwargs.get('name', self.name)
        self.verbose_name = kwargs.get('verbose_name', self.name.title())
        #self.kwargs = kwargs

    def get_param_name(self):
        """Returns the full POST parameter name for this action.

        Defaults to
        ``{{ table.name }}__{{ action.name }}``.
        """
        return "__".join([self.table.name, self.name])

    def action(self, request, obj_data):
        """Action entry point. Overrides base class' action method.

        Accepts a dictionary of data passing it over to the create method
        responsible for the object's destruction.
        """
        return self.create(request, obj_data)

    def create(self, request, obj_data):
        """Required. Creates an object referenced by obj_data.

        Override to provide create functionality specific to your data.
        """
    