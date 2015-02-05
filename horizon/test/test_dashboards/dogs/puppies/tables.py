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

from django.utils.translation import ungettext_lazy

from horizon import tables


class EagerPuppiesTable(tables.DataTable):
    name = tables.Column('name')

    class Meta(object):
        name = 'eager_puppies'
        verbose_name = 'Eager Puppies'


class SellPuppy(tables.DeleteAction):
    @staticmethod
    def action_present(count):
        return ungettext_lazy(
            # Translators: test code, don't really have to translate
            u"Sell Puppy",
            u"Sell Puppies",
            count
        )

    @staticmethod
    def action_past(count):
        return ungettext_lazy(
            # Translators: test code, don't really have to translate
            u"Sold Puppy",
            u"Sold Puppies",
            count
        )

    def delete(self, request, obj_id):
        pass


class LazyPuppiesTable(tables.DataTable):
    name = tables.Column('name')

    class Meta(object):
        name = 'lazy_puppies'
        verbose_name = 'Lazy Puppies'
        table_actions = (SellPuppy,)
        row_actions = (SellPuppy,)
