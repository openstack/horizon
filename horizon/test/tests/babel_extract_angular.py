# -*- encoding: UTF-8 -*-
# Copyright 2015, Rackspace, US, Inc.
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

from six import StringIO

from horizon.test import helpers as test
from horizon.utils.babel_extract_angular import extract_angular

default_keys = []


class ExtractAngularTestCase(test.TestCase):

    def test_extract_no_tags(self):
        buf = StringIO('<html></html>')

        messages = list(extract_angular(buf, default_keys, [], {}))
        self.assertEqual([], messages)

    def test_simple_string(self):
        buf = StringIO(
            """<html><translate>hello world!</translate>'
            <div translate>hello world!</div></html>"""
        )

        messages = list(extract_angular(buf, default_keys, [], {}))
        self.assertEqual(
            [
                (1, u'gettext', 'hello world!', []),
                (2, u'gettext', 'hello world!', [])
            ],
            messages)

    def test_attr_value(self):
        """We should not translate tags that have translate as the value of an
        attribute.
        """
        buf = StringIO('<html><div id="translate">hello world!</div></html>')

        messages = list(extract_angular(buf, [], [], {}))
        self.assertEqual([], messages)

    def test_attr_value_plus_directive(self):
        """Unless they also have a translate directive.
        """
        buf = StringIO(
            '<html><div id="translate" translate>hello world!</div></html>')

        messages = list(extract_angular(buf, [], [], {}))
        self.assertEqual([(1, 'gettext', 'hello world!', [])], messages)

    def test_translate_tag(self):
        buf = StringIO('<html><translate>hello world!</translate></html>')

        messages = list(extract_angular(buf, [], [], {}))
        self.assertEqual([(1, 'gettext', 'hello world!', [])], messages)

    def test_plural_form(self):
        buf = StringIO(
            (
                '<html><translate translate-plural="hello {$count$} worlds!">'
                'hello one world!</translate></html>'
            ))

        messages = list(extract_angular(buf, [], [], {}))
        self.assertEqual(
            [
                (1, 'ngettext',
                 ('hello one world!',
                  'hello {$count$} worlds!'
                  ),
                 [])
            ], messages)

    def test_translate_tag_comments(self):
        buf = StringIO(
            '<html><translate translate-comment='
            '"What a beautiful world">hello world!</translate></html>')

        messages = list(extract_angular(buf, [], [], {}))
        self.assertEqual(
            [
                (1, 'gettext', 'hello world!', ['What a beautiful world'])
            ],
            messages)

    def test_comments(self):
        buf = StringIO(
            '<html><div translate translate-comment='
            '"What a beautiful world">hello world!</div></html>')

        messages = list(extract_angular(buf, [], [], {}))
        self.assertEqual(
            [
                (1, 'gettext', 'hello world!', ['What a beautiful world'])
            ],
            messages)

    def test_multiple_comments(self):
        buf = StringIO(
            '<html><translate '
            'translate-comment="What a beautiful world"'
            'translate-comment="Another comment"'
            '>hello world!</translate></html>')

        messages = list(extract_angular(buf, [], [], {}))
        self.assertEqual(
            [
                (1, 'gettext', 'hello world!',
                 [
                     'What a beautiful world',
                     'Another comment'
                 ])
            ],
            messages)

    def test_filter(self):
        # test also for some forms that should not match
        buf = StringIO(
            """
            <img alt="{$ 'hello world1' | translate $}">
            <p>{$'hello world2'|translate$}</p>
            <img alt="something {$'hello world3'|translate$} something
            {$'hello world4'|translate$}">
            <img alt="{$expr()|translate$}">
            <img alt="{$'some other thing'$}">
            <p>{$'"it\\'s awesome"'|translate$}</p>
            <p>{$"oh \\"hello\\" there"|translate$}</p>
            """
        )

        messages = list(extract_angular(buf, default_keys, [], {}))
        self.assertEqual(
            [
                (2, u'gettext', 'hello world1', []),
                (3, u'gettext', 'hello world2', []),
                (4, u'gettext', 'hello world3', []),
                (4, u'gettext', 'hello world4', []),
                (8, u'gettext', '"it\\\'s awesome"', []),
                (9, u'gettext', 'oh \\"hello\\" there', []),
            ],
            messages)

    def test_trim_translate_tag(self):
        buf = StringIO(
            "<html><translate> \n hello\n world! \n "
            "</translate></html>")

        messages = list(extract_angular(buf, [], [], {}))
        self.assertEqual([(1, 'gettext', 'hello\n world!', [])], messages)

    def test_nested_translate_tag(self):
        buf = StringIO(
            "<html><translate>hello <b>beautiful <i>world</i></b> !"
            "</translate></html>"
        )

        messages = list(extract_angular(buf, [], [], {}))
        self.assertEqual(
            [(1, 'gettext', 'hello <b>beautiful <i>world</i></b> !', [])],
            messages)

    def test_nested_variations(self):
        buf = StringIO(
            '''
            <p translate>To <a href="link">link</a> here</p>
            <p translate>To <!-- a comment!! --> here</p>
            <p translate>To trademark&reg; &#62; &#x3E; here</p>
            '''
        )
        messages = list(extract_angular(buf, [], [], {}))
        self.assertEqual(
            [
                (2, u'gettext', 'To <a href="link">link</a> here', []),
                (3, u'gettext', 'To <!-- a comment!! --> here', []),
                (4, u'gettext', u'To trademark® &#62; &#x3E; here', []),
            ],
            messages)
