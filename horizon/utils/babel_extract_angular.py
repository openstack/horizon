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

try:
    from html.parser import HTMLParser
except ImportError:
    from HTMLParser import HTMLParser


class AngularGettextHTMLParser(HTMLParser):
    """Parse HTML to find translate directives.

    Note: This will not cope with nested tags (which I don't think make any
    sense)
    """

    def __init__(self):
        try:
            super(self.__class__, self).__init__()
        except TypeError:
            HTMLParser.__init__(self)

        self.in_translate = False
        self.data = ''
        self.strings = []
        self.line = 0
        self.plural = False
        self.plural_form = ''
        self.comments = []

    def handle_starttag(self, tag, attrs):
        if tag == 'translate' or \
                (attrs and 'translate' in [attr[0] for attr in attrs]):
                self.in_translate = True
                self.line = self.getpos()[0]

                self.plural_form = ''
                for attr, value in attrs:
                    if attr == 'translate-plural':
                        self.plural = True
                        self.plural_form = value
                    if attr == 'translate-comment':
                        self.comments.append(value)

    def handle_data(self, data):
        if self.in_translate:
            self.data += data

    def handle_endtag(self, tag):
        if self.in_translate:
            if self.plural_form:
                messages = (
                    self.data,
                    self.plural_form
                )
                func_name = u'ngettext'
            else:
                messages = self.data
                func_name = u'gettext'
            self.strings.append(
                (self.line, func_name, messages, self.comments)
            )
            self.in_translate = False
            self.data = ''
            self.comments = []


def extract_angular(fileobj, keywords, comment_tags, options):
    """Extract messages from angular template (HTML) files that use the
    angular-gettext translate directive as per
    https://angular-gettext.rocketeer.be/ .

    :param fileobj: the file-like object the messages should be extracted
                    from
    :param keywords: This is a standard parameter so it isaccepted but ignored.

    :param comment_tags: This is a standard parameter so it is accepted but
                        ignored.
    :param options: Another standard parameter that is accepted but ignored.
    :return: an iterator over ``(lineno, funcname, message, comments)``
             tuples
    :rtype: ``iterator``

    This particular extractor is quite simple because it is intended to only
    deal with angular templates which do not need comments, or the more
    complicated forms of translations.

    A later version will address pluralization.
    """

    parser = AngularGettextHTMLParser()

    for line in fileobj:
        parser.feed(line)

    for string in parser.strings:
        yield(string)
