# Copyright 2016 Hewlett Packard Enterprise Development Company LP
# All Rights Reserved.
#
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

from compressor.signals import post_compress
from django.contrib.staticfiles import finders
from django.core.cache import caches
from django.core.cache.utils import make_template_fragment_key
from django.dispatch import receiver
from django import template

register = template.Library()


@receiver(post_compress)
def update_angular_template_hash(sender, **kwargs):
    """Listen for compress events.

    If the angular templates have been re-compressed, also clear them
    from the Django cache backend.  This is important to allow
    deployers to change a template file, re-compress, and not
    accidentally serve the old Django cached version of that content
    to clients.
    """
    context = kwargs['context']  # context the compressor is working with
    compressed = context['compressed']  # the compressed content
    compressed_name = compressed['name']  # name of the compressed content
    if compressed_name == 'angular_template_cache_preloads':
        # The compressor has modified the angular template cache preloads
        # which are cached in the 'default' Django cache. Fetch that cache.
        cache = caches['default']

        # generate the same key as used in _scripts.html when caching the
        # preloads
        theme = context['THEME']  # current theme being compressed
        key = make_template_fragment_key(
            "angular",
            ['template_cache_preloads', theme]
        )

        # if template preloads have been cached, clear them
        if cache.get(key):
            cache.delete(key)


@register.filter(name='angular_escapes')
def angular_escapes(value):
    """Provide a basic filter to allow angular template content for Angular.

    Djangos 'escapejs' is too aggressive and inserts unicode.
    It provide a basic filter to allow angular template content to be used
    within javascript strings.

    Args:
        value: a string

    Returns:
        string with escaped values
    """
    return value \
        .replace('\\', '\\\\') \
        .replace('"', '\\"') \
        .replace("'", "\\'") \
        .replace("\n", "\\n") \
        .replace("\r", "\\r")


@register.inclusion_tag('angular/angular_templates.html', takes_context=True)
def angular_templates(context):
    """Generate a dictionary of template contents for all static HTML templates.

    If the template has been overridden by a theme, load the
    override contents instead of the original HTML file.
    One use for this is to pre-populate the angular template cache.

    Args:
        context: the context of the current Django template

    Returns: an object containing
     angular_templates: dictionary of angular template contents
      - key is the template's static path,
      - value is a string of HTML template contents
    """
    template_paths = context['HORIZON_CONFIG']['external_templates']
    all_theme_static_files = context['HORIZON_CONFIG']['theme_static_files']
    this_theme_static_files = all_theme_static_files[context['THEME']]
    template_overrides = this_theme_static_files['template_overrides']
    angular_templates = {}

    for relative_path in template_paths:

        template_static_path = context['STATIC_URL'] + relative_path

        # If the current theme overrides this template, use the theme
        # content instead of the original file content
        if relative_path in template_overrides:
            relative_path = template_overrides[relative_path]

        result = []
        for finder in finders.get_finders():
            result.extend(finder.find(relative_path, True))
        path = result[-1]
        try:
            with open(path) as template_file:
                angular_templates[template_static_path] = template_file.read()
        except (OSError, IOError):
            # Failed to read template, leave the template dictionary blank
            # If the caller is using this dictionary to pre-populate a cache
            # there will simply be no pre-loaded version for this template.
            pass

    templates = [(key, value) for key, value in angular_templates.items()]
    templates.sort(key=lambda item: item[0])

    return {
        'angular_templates': templates
    }
