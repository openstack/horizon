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

import functools

import futurist


def call_functions_parallel(*worker_defs):
    """Call specified functions in parallel.

    :param *worker_defs: Each positional argument can be either of
        a function to be called or a tuple which consists of a function,
        a list of positional arguments) and keyword arguments (optional).
        If you need to pass arguments, you need to pass a tuple.
        Example usages are like:
           call_functions_parallel(func1, func2, func3)
           call_functions_parallel(func1, (func2, [1, 2]))
           call_functions_parallel((func1, [], {'a': 1}),
                                   (func2, [], {'a': 2, 'b': 10}))
    :returns: a tuple of values returned from individual functions.
        None is returned if a corresponding function does not return.
        It is better to return values other than None from individual
        functions.
    """
    # TODO(amotoki): Needs to figure out what max_workers can be specified.
    # According to e0ne, the apache default configuration in devstack  allows
    # only 10 threads. What happens if max_worker=11 is specified?
    max_workers = len(worker_defs)
    # Prepare a list with enough length.
    futures = [None] * len(worker_defs)
    with futurist.ThreadPoolExecutor(max_workers=max_workers) as e:
        for index, func_def in enumerate(worker_defs):
            if callable(func_def):
                func_def = [func_def]
            args = func_def[1] if len(func_def) > 1 else []
            kwargs = func_def[2] if len(func_def) > 2 else {}
            func = functools.partial(func_def[0], *args, **kwargs)
            futures[index] = e.submit(fn=func)

    return tuple(f.result() for f in futures)
