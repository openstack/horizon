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

from horizon import tables


class EagerPuppiesTable(tables.DataTable):
    name = tables.Column('name')

    class Meta:
        name = 'eager_puppies'
        verbose_name = 'Eager Puppies'


class SellPuppy(tables.DeleteAction):
    data_type_singular = 'Puppy'
    data_type_plural = 'Puppies'

    def delete(self, request, obj_id):
        pass


class LazyPuppiesTable(tables.DataTable):
    name = tables.Column('name')

    class Meta:
        name = 'lazy_puppies'
        verbose_name = 'Lazy Puppies'
        table_actions = (SellPuppy,)
        row_actions = (SellPuppy,)
