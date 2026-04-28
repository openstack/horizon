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

import logging

from django.template.base import Lexer
from django.template.base import TokenType

from django.utils.encoding import smart_str
from django.utils.translation import trim_whitespace

from django.utils.translation.template import block_re
from django.utils.translation.template import constant_re
from django.utils.translation.template import endblock_re
from django.utils.translation.template import inline_re
from django.utils.translation.template import plural_re


LOG = logging.getLogger(__name__)

TOKEN_TEXT = TokenType.TEXT
TOKEN_VAR = TokenType.VAR
TOKEN_BLOCK = TokenType.BLOCK


def extract_django(fileobj, keywords, comment_tags, options):
    """Extract messages from Django template files.

    :param fileobj: the file-like object the messages should be extracted from
    :param keywords: a list of keywords (i.e. function names) that should
                     be recognized as translation functions
    :param comment_tags: a list of translator tags to search for and
                         include in the results
    :param options: a dictionary of additional options (e.g.: encoding)
    :return: an iterator over ``(lineno, funcname, message, comments)`` tuples
    :rtype: ``iterator``
    """
    encoding = options.get('encoding', 'utf8')
    try:
        content = fileobj.read().decode(encoding)
    except UnicodeDecodeError as e:
        # Get the filename if available, otherwise use a placeholder
        file = getattr(fileobj, 'name', 'unknown file')
        LOG.warning("Skipping %(file)s. Could not decode using %(encoding)s: "
                    "%(exc)s", {'file': file, 'encoding': encoding, 'exc': e})
        return

    # Initialize Lexer
    lexer = Lexer(content)
    tokens = lexer.tokenize()

    state = {
        'intrans': False,
        'inplural': False,
        'trimmed': False,
        'message_context': None,
        'singular': [],
        'plural': [],
        'lineno': 1
    }

    for t in tokens:
        state['lineno'] += t.contents.count('\n')

        if state['intrans']:
            yield from handle_intrans_token(t, state)
        else:
            yield from handle_outside_token(t, state)


def handle_intrans_token(t, state):
    """Handles tokens when inside a trans/blocktrans block."""
    if t.token_type == TOKEN_BLOCK:
        endbmatch = endblock_re.match(t.contents)
        pluralmatch = plural_re.match(t.contents)

        if endbmatch:
            yield generate_block_yield(state)
            # Reset state
            state.update({'intrans': False, 'inplural': False,
                          'message_context': None,
                          'singular': [], 'plural': []})
        elif pluralmatch:
            state['inplural'] = True
        else:
            raise SyntaxError('Translation blocks must not include '
                              'other block tags: %s' % t.contents)

    elif t.token_type == TOKEN_VAR:
        target = state['plural'] if state['inplural'] else state['singular']
        target.append('%%(%s)s' % t.contents)

    elif t.token_type == TOKEN_TEXT:
        target = state['plural'] if state['inplural'] else state['singular']
        target.append(t.contents)


def handle_outside_token(t, state):
    """Handles tokens when outside a translation block."""
    if t.token_type == TOKEN_BLOCK:
        imatch = inline_re.match(t.contents)
        bmatch = block_re.match(t.contents)
        cmatches = constant_re.findall(t.contents)

        if imatch:
            g = strip_quotes(imatch.group(1))
            message_context = imatch.group(3)
            if message_context:
                yield (state['lineno'], 'pgettext',
                       [smart_str(message_context[1:-1]), smart_str(g)], [])
            else:
                yield state['lineno'], None, smart_str(g), []

        elif bmatch:
            if bmatch.group(2):
                state['message_context'] = bmatch.group(2)[1:-1]
            for fmatch in constant_re.findall(t.contents):
                yield state['lineno'], None, smart_str(strip_quotes(fmatch)), []
            state.update({'intrans': True, 'inplural': False,
                          'singular': [], 'plural': [],
                          'trimmed': 'trimmed' in t.split_contents()})

        elif cmatches:
            for cmatch in cmatches:
                yield state['lineno'], None, smart_str(strip_quotes(cmatch)), []

    elif t.token_type == TOKEN_VAR:
        parts = t.contents.split('|')
        cmatch = constant_re.match(parts[0])
        if cmatch:
            yield (state['lineno'], None,
                   smart_str(strip_quotes(cmatch.group(1))), [])

        for p in parts[1:]:
            if p.find(':_(') >= 0:
                p1 = p.split(':', 1)[1]
                if p1[0] == '_':
                    p1 = p1[1:]
                if p1[0] == '(':
                    p1 = p1.strip('()')
                yield state['lineno'], None, smart_str(strip_quotes(p1)), []


def generate_block_yield(state):
    """Helper to construct the yield tuple for blocktrans tags."""
    lineno = state['lineno']
    singular_str = smart_str(join_tokens(state['singular'], state['trimmed']))
    context = state['message_context']

    if state['inplural']:
        plural_str = smart_str(join_tokens(state['plural'], state['trimmed']))
        if context:
            return (lineno, 'npgettext',
                    [smart_str(context), singular_str, plural_str], [])
        return lineno, 'ngettext', (singular_str, plural_str), []

    if context:
        return lineno, 'pgettext', [smart_str(context), singular_str], []
    return lineno, None, singular_str, []


def join_tokens(tokens, trim=False):
    message = ''.join(tokens)
    if trim:
        message = trim_whitespace(message)
    return message


def strip_quotes(s):
    if (s[0] == s[-1]) and s.startswith(("'", '"')):
        return s[1:-1]
    return s
