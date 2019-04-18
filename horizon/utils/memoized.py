# Copyright 2012 Nebula, Inc.
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

import collections
import functools
import threading
import warnings
import weakref

from django.conf import settings


class UnhashableKeyWarning(RuntimeWarning):
    """Raised when trying to memoize a function with an unhashable argument."""


def _try_weakref(arg, remove_callback):
    """Return a weak reference to arg if possible, or arg itself if not."""
    try:
        arg = weakref.ref(arg, remove_callback)
    except TypeError:
        # Not all types can have a weakref. That includes strings
        # and floats and such, so just pass them through directly.
        pass
    return arg


def _get_key(args, kwargs, remove_callback):
    """Calculate the cache key, using weak references where possible."""
    # Use tuples, because lists are not hashable.
    weak_args = tuple(_try_weakref(arg, remove_callback) for arg in args)
    # Use a tuple of (key, values) pairs, because dict is not hashable.
    # Sort it, so that we don't depend on the order of keys.
    weak_kwargs = tuple(sorted(
        (key, _try_weakref(value, remove_callback))
        for (key, value) in kwargs.items()))
    return weak_args, weak_kwargs


def memoized(func=None, max_size=None):
    """Decorator that caches function calls.

    Caches the decorated function's return value the first time it is called
    with the given arguments.  If called later with the same arguments, the
    cached value is returned instead of calling the decorated function again.

    It operates as a LRU cache and keeps up to the max_size value of cached
    items, always clearing oldest items first.

    The cache uses weak references to the passed arguments, so it doesn't keep
    them alive in memory forever.
    """

    def decorate(func):

        # The dictionary in which all the data will be cached. This is a
        # separate instance for every decorated function, and it's stored in a
        # closure of the wrapped function.
        cache = collections.OrderedDict()
        locks = collections.defaultdict(threading.Lock)
        if max_size:
            max_cache_size = max_size
        else:
            max_cache_size = settings.MEMOIZED_MAX_SIZE_DEFAULT

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            # We need to have defined key early, to be able to use it in the
            # remove() function, but we calculate the actual value of the key
            # later on, because we need the remove() function for that.
            key = None

            def remove(ref):
                """A callback to remove outdated items from cache."""
                try:
                    # The key here is from closure, and is calculated later.
                    del cache[key]
                    del locks[key]
                except KeyError:
                    # Some other weak reference might have already removed that
                    # key -- in that case we don't need to do anything.
                    pass

            key = _get_key(args, kwargs, remove)
            try:
                with locks[key]:
                    try:
                        # We want cache hit to be as fast as possible, and
                        # don't really care much about the speed of a cache
                        # miss, because it will only happen once and likely
                        # calls some external API, database, or some other slow
                        # thing. That's why the hit is in straightforward code,
                        # and the miss is in an exception.
                        # We also want to pop the key and reset it to make sure
                        # the position it has in the order updates.
                        value = cache[key] = cache.pop(key)
                    except KeyError:
                        value = cache[key] = func(*args, **kwargs)
            except TypeError:
                # The calculated key may be unhashable when an unhashable
                # object, such as a list, is passed as one of the arguments. In
                # that case, we can't cache anything and simply always call the
                # decorated function.
                warnings.warn(
                    "The key of %s %s is not hashable and cannot be memoized: "
                    "%r\n" % (func.__module__, func.__name__, key),
                    UnhashableKeyWarning, 2)
                value = func(*args, **kwargs)

            while len(cache) > max_cache_size:
                try:
                    popped_tuple = cache.popitem(last=False)
                    locks.pop(popped_tuple[0], None)
                except KeyError:
                    pass

            return value
        return wrapped
    if func and callable(func):
        return decorate(func)
    return decorate


# We can use @memoized for methods now too, because it uses weakref and so
# it doesn't keep the instances in memory forever. We might want to separate
# them in the future, however.
memoized_method = memoized
