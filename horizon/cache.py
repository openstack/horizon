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

from django.conf import settings
from django.core.cache import caches
from django.core.cache.utils import make_template_fragment_key


def cleanup_angular_template_cache(theme):
    # The compressor has modified the angular template cache preloads
    # which are cached in the 'COMPRESS_CACHE_BACKEND' Django cache.
    django_cache = caches[settings.COMPRESS_CACHE_BACKEND]

    # generate the same key as used in _scripts.html when caching the
    # preloads
    key = make_template_fragment_key(
        "angular",
        ['template_cache_preloads', theme]
    )

    # if template preloads have been cached, clear them
    if django_cache.get(key):
        # Set to None because memcached doesn't remove records immediately
        django_cache.set(key, None)
