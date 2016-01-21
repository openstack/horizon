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

from horizon.utils import file_discovery as fd
import unittest

base_path = 'some_root/fake_static_files/'

test_structure = [
    (
        'some_root/fake_static_files/a',
        [
            'a.controller.js',
            'a.controller.spec.js',
            'a.directive.js',
            'a.directive.spec.js',
            'a.html',
            'a.mock.js',
            'a.module.js',
            'a.module.spec.js',
        ]
    ),
    (
        'some_root/fake_static_files/b',
        [
            'README.txt',
            'LICENCE',
            'b.controller.js',
            'b.controller.spec.js',
            'b.directive.js',
            'b.directive.spec.js',
            'b.html',
            'b.mock.js',
            'b.module.js',
            'b.spec.js',
        ]
    )
]


def fake_walk(path):
    for root, files in test_structure:
        if root.startswith(path):
            yield root, [], files


def another_fake_walk(path):
    for root, files in reversed(test_structure):
        if root.startswith(path):
            yield root, [], files


class FinderTests(unittest.TestCase):
    def setUp(self):
        self.old_walk = fd.walk
        fd.walk = fake_walk

    def tearDown(self):
        fd.walk = self.old_walk

    #
    # discover_files()
    #
    def test_find_all(self):
        """Find all files
        """
        files = fd.discover_files(base_path)
        self.assertEqual(len(files), 18)

    def test_find_a(self):
        """Find all files in folder `a`
        """
        files = fd.discover_files(base_path, sub_path='a')
        self.assertEqual(len(files), 8)

    def test_find_b(self):
        """Find all files in folder `b`
        """
        files = fd.discover_files(base_path, sub_path='b')
        self.assertEqual(len(files), 10)

    def test_find_all_js(self):
        """Find all files with extension of `.js`
        """
        files = fd.discover_files(base_path, ext='.js')
        self.assertEqual(len(files), 14)

    def test_find_all_html(self):
        """Find all files with extension of `.html`
        """
        files = fd.discover_files(base_path, ext='.html')
        self.assertEqual(len(files), 2)

    def test_find_all_js_in_a(self):
        """Find all files with extension of `.js` in folder a
        """
        files = fd.discover_files(base_path, sub_path='b', ext='.js')
        self.assertEqual(len(files), 7)

    def test_find_all_html_in_a(self):
        """Find all files with extension of `.html` in folder a
        """
        files = fd.discover_files(base_path, sub_path='b', ext='.html')
        self.assertEqual(len(files), 1)

    def test_find_all_file_trim_base_path(self):
        """Find all files in folder, trim base path
        """
        files = fd.discover_files(base_path, sub_path='a', trim_base_path=True)
        self.assertTrue(files[0].startswith('a/'))

        files = fd.discover_files(base_path, sub_path='b', trim_base_path=True)
        self.assertTrue(files[0].startswith('b/'))

    #
    # sort_js_files()
    #
    def test_sort_js_files(self):
        """Sort all JavaScript files
        """
        files = fd.discover_files(base_path, ext='.js')
        sources, mocks, specs = fd.sort_js_files(files)

        self.assertEqual(len(sources), 6)
        self.assertEqual(len(mocks), 2)
        self.assertEqual(len(specs), 6)

        self.assertTrue(sources[0].endswith('.module.js'))
        self.assertTrue(sources[1].endswith('.module.js'))

        self.assertTrue(sources[2].endswith('.controller.js'))
        self.assertTrue(sources[3].endswith('.directive.js'))
        self.assertTrue(sources[4].endswith('.controller.js'))
        self.assertTrue(sources[5].endswith('.directive.js'))

        self.assertTrue(mocks[0].endswith('.mock.js'))
        self.assertTrue(mocks[1].endswith('.mock.js'))

        self.assertTrue(specs[0].endswith('.spec.js'))
        self.assertTrue(specs[1].endswith('.spec.js'))
        self.assertTrue(specs[2].endswith('.spec.js'))
        self.assertTrue(specs[3].endswith('.spec.js'))
        self.assertTrue(specs[4].endswith('.spec.js'))
        self.assertTrue(specs[5].endswith('.spec.js'))

    #
    # discover_static_files()
    #
    def test_discover_all_static_files(self):
        """Find all static files
        """
        sources, mocks, specs, templates = fd.discover_static_files(base_path)
        self.assertEqual(len(sources), 6)
        self.assertEqual(len(mocks), 2)
        self.assertEqual(len(specs), 6)
        self.assertEqual(len(templates), 2)

        self.assertTrue(sources[0].endswith('.module.js'))
        self.assertTrue(sources[1].endswith('.module.js'))

        self.assertTrue(sources[2].endswith('.controller.js'))
        self.assertTrue(sources[3].endswith('.directive.js'))
        self.assertTrue(sources[4].endswith('.controller.js'))
        self.assertTrue(sources[5].endswith('.directive.js'))

        self.assertTrue(mocks[0].endswith('.mock.js'))
        self.assertTrue(mocks[1].endswith('.mock.js'))

        self.assertTrue(specs[0].endswith('.spec.js'))
        self.assertTrue(specs[1].endswith('.spec.js'))
        self.assertTrue(specs[2].endswith('.spec.js'))
        self.assertTrue(specs[3].endswith('.spec.js'))
        self.assertTrue(specs[4].endswith('.spec.js'))
        self.assertTrue(specs[5].endswith('.spec.js'))

        self.assertTrue(templates[0].endswith('.html'))
        self.assertTrue(templates[1].endswith('.html'))

    #
    # populate_horizon_config()
    #
    def test_populate_horizon_config(self):
        """Populate horizon config
        """
        horizon_config = {}

        fd.populate_horizon_config(horizon_config, base_path)
        sources = horizon_config['js_files']
        test_files = horizon_config['js_spec_files']
        templates = horizon_config['external_templates']

        self.assertEqual(len(sources), 6)
        self.assertEqual(len(test_files), 8)
        self.assertEqual(len(templates), 2)

        self.assertTrue(sources[0].endswith('a.module.js'))
        self.assertTrue(sources[1].endswith('b.module.js'))

        self.assertTrue(sources[2].endswith('a.controller.js'))
        self.assertTrue(sources[3].endswith('a.directive.js'))
        self.assertTrue(sources[4].endswith('b.controller.js'))
        self.assertTrue(sources[5].endswith('b.directive.js'))

        self.assertTrue(test_files[0].endswith('.mock.js'))
        self.assertTrue(test_files[1].endswith('.mock.js'))

        self.assertTrue(test_files[2].endswith('.spec.js'))
        self.assertTrue(test_files[3].endswith('.spec.js'))
        self.assertTrue(test_files[4].endswith('.spec.js'))
        self.assertTrue(test_files[5].endswith('.spec.js'))
        self.assertTrue(test_files[6].endswith('.spec.js'))
        self.assertTrue(test_files[7].endswith('.spec.js'))

        self.assertTrue(templates[0].endswith('.html'))
        self.assertTrue(templates[1].endswith('.html'))

    #
    # populate_horizon_config()
    #
    def test_populate_horizon_config_consistent_result(self):
        fd.walk = another_fake_walk
        horizon_config = {}

        fd.populate_horizon_config(horizon_config, base_path)
        sources = horizon_config['js_files']
        test_files = horizon_config['js_spec_files']
        templates = horizon_config['external_templates']

        self.assertEqual(len(sources), 6)
        self.assertEqual(len(test_files), 8)
        self.assertEqual(len(templates), 2)

        self.assertTrue(sources[0].endswith('a.module.js'))
        self.assertTrue(sources[1].endswith('b.module.js'))

        self.assertTrue(sources[2].endswith('a.controller.js'))
        self.assertTrue(sources[3].endswith('a.directive.js'))
        self.assertTrue(sources[4].endswith('b.controller.js'))
        self.assertTrue(sources[5].endswith('b.directive.js'))

        self.assertTrue(test_files[0].endswith('.mock.js'))
        self.assertTrue(test_files[1].endswith('.mock.js'))

        self.assertTrue(test_files[2].endswith('.spec.js'))
        self.assertTrue(test_files[3].endswith('.spec.js'))
        self.assertTrue(test_files[4].endswith('.spec.js'))
        self.assertTrue(test_files[5].endswith('.spec.js'))
        self.assertTrue(test_files[6].endswith('.spec.js'))
        self.assertTrue(test_files[7].endswith('.spec.js'))

        self.assertTrue(templates[0].endswith('.html'))
        self.assertTrue(templates[1].endswith('.html'))
