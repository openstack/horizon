#!/usr/bin/env python
# coding: utf-8

# Copyright 2015 IBM Corp.
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import argparse

import babel.messages.catalog as catalog
import babel.messages.pofile as pofile

# NOTE: This implementation has been superseded by the pseudo_translate
# management command, and will be removed in Queens (13.0) when run_tests.sh
# is also removed.


def translate(segment):
    prefix = u""
    # When the id starts with a newline the mo compiler enforces that
    # the translated message must also start with a newline.  Make
    # sure that doesn't get broken when prepending the bracket.
    if segment.startswith('\n'):
        prefix = u"\n"
    orig_size = len(segment)
    # Add extra expansion space based on recommendation from
    # http://www-01.ibm.com/software/globalization/guidelines/a3.html
    if orig_size < 20:
        multiplier = 1
    elif orig_size < 30:
        multiplier = 0.8
    elif orig_size < 50:
        multiplier = 0.6
    elif orig_size < 70:
        multiplier = 0.4
    else:
        multiplier = 0.3
    extra_length = int(max(0, (orig_size * multiplier) - 10))
    extra_chars = "~" * extra_length
    return u"{0}[~{1}~您好яшçあ{2}]".format(prefix, segment, extra_chars)


def main():
    # Check arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('pot_filename', type=argparse.FileType('r'))
    parser.add_argument('po_filename', type=argparse.FileType('w'))
    parser.add_argument('locale')
    args = parser.parse_args()

    # read POT file
    pot_cat = pofile.read_po(args.pot_filename, ignore_obsolete=True)

    # Create the new Catalog
    new_cat = catalog.Catalog(locale=args.locale,
                              last_translator="pseudo.py",
                              charset="utf-8")
    num_plurals = new_cat.num_plurals

    # Process messages from template
    for msg in pot_cat:
        if msg.pluralizable:
            msg.string = [translate(u"{}:{}".format(i, msg.id[0]))
                          for i in range(num_plurals)]
        else:
            msg.string = translate(msg.id)
        new_cat[msg.id] = msg

    # Write "translated" PO file
    pofile.write_po(args.po_filename, new_cat, ignore_obsolete=True)


if __name__ == '__main__':
    main()
