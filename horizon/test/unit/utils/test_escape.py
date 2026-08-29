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

import json

from horizon.test import helpers as test
from horizon.utils import escape


class JsonDumpsForScriptTests(test.TestCase):

    def test_script_tag_cannot_break_out(self):
        payload = '</script><script>alert(1)</script>'
        dumped = escape.json_dumps_for_script([{'name': payload}])
        self.assertNotIn('</script>', dumped)
        self.assertNotIn('<', dumped)
        self.assertNotIn('>', dumped)

    def test_ampersand_is_escaped(self):
        self.assertNotIn('&', escape.json_dumps_for_script({'name': 'a&b'}))

    def test_decoded_value_is_unchanged(self):
        value = [{'name': '</script>', 'description': 'a & b <c>'}]
        self.assertEqual(value,
                         json.loads(escape.json_dumps_for_script(value)))

    def test_output_is_still_valid_json(self):
        value = {'flavors': [1, 2], 'name': None, 'ok': True}
        self.assertEqual(value,
                         json.loads(escape.json_dumps_for_script(value)))
