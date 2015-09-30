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


class ObjDictWrapper(dict):
    """ObjDictWrapper is a container that provides both dictionary-like and
    object-like attribute access.
    """
    def __getattr__(self, item):
        if item in self:
            return self[item]
        else:
            raise AttributeError(item)

    def __setattr__(self, item, value):
        self[item] = value

    def __repr__(self):
        return '<ObjDictWrapper %s>' % super(ObjDictWrapper, self).__repr__()
