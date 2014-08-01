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

from horizon import tabs
from horizon.test.test_dashboards.dogs.puppies import tables
from horizon.test import utils


class EagerPuppiesTab(tabs.TableTab):
    table_classes = (tables.EagerPuppiesTable,)
    name = 'Eager Puppies'
    slug = 'eager_puppies'
    template_name = 'horizon/common/_detail_table.html'

    def get_eager_puppies_data(self):
        return []


class LazyPuppiesTab(tabs.TableTab):
    table_classes = (tables.LazyPuppiesTable,)
    name = 'Lazy Puppies'
    slug = 'lazy_puppies'
    preload = False
    template_name = 'horizon/common/_detail_table.html'

    def get_lazy_puppies_data(self):
        return [utils.ObjDictWrapper(id=1, name='Caesar'),
                utils.ObjDictWrapper(id=2, name='Augustus')]


class PuppiesTabs(tabs.TabGroup):
    slug = 'puppies_tabs'
    tabs = (EagerPuppiesTab, LazyPuppiesTab)
