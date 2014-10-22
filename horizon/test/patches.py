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

import re

from six.moves import html_parser as _HTMLParser


def parse_starttag_patched(self, i):
    """This method is a patched version of the parse_starttag method from
    django.utils.html_parser.HTMLParser class, used to patch bug 1273943.
    The code is taken from file django/utils/html_parser.py, commit 6bc1b22299.
    """
    self.__starttag_text = None
    endpos = self.check_for_whole_start_tag(i)
    if endpos < 0:
        return endpos
    rawdata = self.rawdata
    self.__starttag_text = rawdata[i:endpos]

    # Now parse the data between i+1 and j into a tag and attrs
    attrs = []
    tagfind = re.compile('([a-zA-Z][-.a-zA-Z0-9:_]*)(?:\s|/(?!>))*')
    match = tagfind.match(rawdata, i + 1)
    assert match, 'unexpected call to parse_starttag()'
    k = match.end()
    self.lasttag = tag = match.group(1).lower()

    while k < endpos:
        m = _HTMLParser.attrfind.match(rawdata, k)
        if not m:
            break
        attrname, rest, attrvalue = m.group(1, 2, 3)
        if not rest:
            attrvalue = None
        elif (attrvalue[:1] == '\'' == attrvalue[-1:] or
              attrvalue[:1] == '"' == attrvalue[-1:]):
            attrvalue = attrvalue[1:-1]
        if attrvalue:
            attrvalue = self.unescape(attrvalue)
        attrs.append((attrname.lower(), attrvalue))
        k = m.end()

    end = rawdata[k:endpos].strip()
    if end not in (">", "/>"):
        lineno, offset = self.getpos()
        if "\n" in self.__starttag_text:
            lineno = lineno + self.__starttag_text.count("\n")
            offset = (len(self.__starttag_text)
                      - self.__starttag_text.rfind("\n"))
        else:
            offset = offset + len(self.__starttag_text)
        self.error("junk characters in start tag: %r"
                   % (rawdata[k:endpos][:20],))
    if end.endswith('/>'):
        # XHTML-style empty tag: <span attr="value" />
        self.handle_startendtag(tag, attrs)
    else:
        self.handle_starttag(tag, attrs)
        if tag in self.CDATA_CONTENT_ELEMENTS:
            self.set_cdata_mode(tag)    # <--------------------------- Changed
    return endpos
