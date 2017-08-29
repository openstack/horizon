# coding: utf-8

# Copyright 2016 Cisco Systems, Inc.
# Copyright 2015 IBM Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from subprocess import call

import babel.messages.catalog as catalog
import babel.messages.pofile as babel_pofile
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import translation

LANGUAGE_CODES = [language[0] for language in settings.LANGUAGES
                  if language[0] != 'en']
POTFILE = "{module}/locale/{domain}.pot"
POFILE = "{module}/locale/{locale}/LC_MESSAGES/{domain}.po"
DOMAINS = ['django', 'djangojs']
MODULES = ['openstack_dashboard', 'horizon']


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


class Command(BaseCommand):
    help = 'Update a translation catalog for a specified language'

    def add_arguments(self, parser):
        parser.add_argument('-l', '--language', choices=LANGUAGE_CODES,
                            default=LANGUAGE_CODES, nargs='+',
                            metavar='LANG',
                            help=("The language code(s) to pseudo translate. "
                                  "Available languages are: %s"
                                  % ', '.join(sorted(LANGUAGE_CODES))))
        parser.add_argument('-m', '--module', type=str, nargs='+',
                            default=MODULES,
                            help=("The target python module(s) to extract "
                                  "strings from. "
                                  "Default: %s" % MODULES))
        parser.add_argument('-d', '--domain', choices=DOMAINS,
                            nargs='+', default=DOMAINS,
                            metavar='DOMAIN',
                            help=("Domain(s) of the .POT file. "
                                  "Default: %s" % DOMAINS))
        parser.add_argument('--pseudo', action='store_true',
                            help=("Creates a pseudo translation for the "
                                  "specified locale, to check for "
                                  "translatable string coverage"))

    def handle(self, *args, **options):
        for module in options['module']:
            for domain in options['domain']:
                potfile = POTFILE.format(module=module, domain=domain)

                for language in options['language']:
                    # Get the locale code for the language code given and
                    # work around broken django conversion function
                    locales = {'ko': 'ko_KR', 'pl': 'pl_PL', 'tr': 'tr_TR'}
                    locale = locales.get(language,
                                         translation.to_locale(language))
                    pofile = POFILE.format(module=module, locale=locale,
                                           domain=domain)

                    # If this isn't a pseudo translation, execute pybabel
                    if not options['pseudo']:
                        if not os.path.exists(pofile):
                            with open(pofile, 'wb') as fobj:
                                fobj.write(b'')

                        cmd = ('pybabel update -l {locale} -i {potfile} '
                               '-o {pofile}').format(locale=locale,
                                                     potfile=potfile,
                                                     pofile=pofile)
                        call(cmd, shell=True)
                        continue

                    # Pseudo translation logic
                    with open(potfile, 'r') as f:
                        pot_cat = babel_pofile.read_po(f, ignore_obsolete=True)

                    new_cat = catalog.Catalog(locale=locale,
                                              last_translator="pseudo.py",
                                              charset="utf-8")
                    num_plurals = new_cat.num_plurals

                    for msg in pot_cat:
                        if msg.pluralizable:
                            msg.string = [
                                translate(u"{}:{}".format(i, msg.id[0]))
                                for i in range(num_plurals)]
                        else:
                            msg.string = translate(msg.id)
                        new_cat[msg.id] = msg

                    with open(pofile, 'w') as f:
                        babel_pofile.write_po(f, new_cat, ignore_obsolete=True)
