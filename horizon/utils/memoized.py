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


def memoized(func):
    """Decorator that caches function calls.

    Caches the decorated function's return value the first time it is called
    with the given arguments.  If called later with the same arguments, the
    cached value is returned instead of calling the decorated function again.

    The cache uses weak references to the passed arguments, so it doesn't keep
    them alive in memory forever.
    """
    # The dictionary in which all the data will be cached. This is a separate
    # instance for every decorated function, and it's stored in a closure of
    # the wrapped function.
    cache = {}
    locks = collections.defaultdict(threading.Lock)

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
                    # We want cache hit to be as fast as possible, and don't
                    # really care much about the speed of a cache miss, because
                    # it will only happen once and likely calls some external
                    # API, database, or some other slow thing. That's why the
                    # hit is in straightforward code, and the miss is in an
                    # exception.
                    value = cache[key]
                except KeyError:
                    value = cache[key] = func(*args, **kwargs)
        except TypeError:
            # The calculated key may be unhashable when an unhashable
            # object, such as a list, is passed as one of the arguments. In
            # that case, we can't cache anything and simply always call the
            # decorated function.
            warnings.warn(
                "The key %r is not hashable and cannot be memoized."
                % (key,), UnhashableKeyWarning, 2)
            value = func(*args, **kwargs)
        return value
    return wrapped

# We can use @memoized for methods now too, because it uses weakref and so
# it doesn't keep the instances in memory forever. We might want to separate
# them in the future, however.
memoized_method = memoized


def memoized_with_request(request_func, request_index=0):
    """Decorator for caching functions which receive a request argument

    memoized functions with a request argument are memoized only during the
    rendering of a single view because the request argument is a new request
    instance on each view.

    If you want a function to be memoized for multiple views use this
    decorator.

    It replaces the request argument in the call to the decorated function
    with the result of calling request_func on that request object.

    request_function is a function which will receive the request argument.

    request_index indicates which argument of the decorated function is the
    request object to pass into request_func, which will also be replaced
    by the result of request_func being called.

    your memoized function will instead receive request_func(request)
    passed as argument at the request_index.

    The intent of that function is to extract the information needed from the
    request, and thus the memoizing will operate just on that part of the
    request that is relevant to the function being memoized.

    short example::

        @memoized
        def _get_api_client(username, token_id, project_id, auth_url)
            return api_client.Client(username, token_id, project_id, auth_url)

        def get_api_client(request):
            return _api_client(request.user.username,
                               request.user.token.id,
                               request.user.tenant_id)

        @memoized_with_request(get_api_client)
        def some_api_function(api_client, *args, **kwargs):
            # is like returning get_api_client(
            #    request).some_method(*args, **kwargs)
            # but with memoization.
            return api_client.some_method(*args, **kwargs)

        @memoized_with_request(get_api_client, 1)
        def some_other_funt(param, api_client, other_param):
            # The decorated function will be called this way:
            #     some_other_funt(param, request, other_param)
            # but will be called behind the scenes this way:
            #     some_other_funt(param, get_api_client(request), other_param)
            return api_client.some_method(param, other_param)

    See openstack_dashboard.api.nova for a complete example.
    """
    def wrapper(func):
        memoized_func = memoized(func)

        @functools.wraps(func)
        def wrapped(*args, **kwargs):
            args = list(args)
            request = args.pop(request_index)
            args.insert(request_index, request_func(request))
            return memoized_func(*args, **kwargs)

        return wrapped
    return wrapper
