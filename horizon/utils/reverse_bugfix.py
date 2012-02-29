"""
Bugfix for issue #15900: https://code.djangoproject.com/ticket/15900.

This code is largely reproduced from
https://code.djangoproject.com/browser/django/trunk/django/core/urlresolvers.py
and is the work of Django's authors:
https://code.djangoproject.com/browser/django/trunk/AUTHORS

It is licensed under Django's BSD license, available here:
https://code.djangoproject.com/browser/django/trunk/LICENSE

To use, simply import this code in your project's root URLconf file before
defining any URL patterns.
"""

from django.core import urlresolvers

if not hasattr(urlresolvers.RegexURLResolver, "_reverse_with_prefix"):
    import re

    from django.conf import urls
    from django.utils.datastructures import MultiValueDict
    from django.utils.encoding import iri_to_uri, force_unicode
    from django.utils.regex_helper import normalize

    def _populate(self):
        lookups = MultiValueDict()
        namespaces = {}
        apps = {}
        for pattern in reversed(self.url_patterns):
            p_pattern = pattern.regex.pattern
            if p_pattern.startswith('^'):
                p_pattern = p_pattern[1:]
            if isinstance(pattern, urlresolvers.RegexURLResolver):
                if pattern.namespace:
                    namespaces[pattern.namespace] = (p_pattern, pattern)
                    if pattern.app_name:
                        apps.setdefault(pattern.app_name, []) \
                            .append(pattern.namespace)
                else:
                    parent = normalize(pattern.regex.pattern)
                    for name in pattern.reverse_dict:
                        for matches, pat, defaults in \
                                pattern.reverse_dict.getlist(name):
                            new_matches = []
                            for piece, p_args in parent:
                                vals = [(piece + suffix, p_args + args) for \
                                        (suffix, args) in matches]
                                new_matches.extend(vals)
                            lookup_list = (new_matches, p_pattern + pat,
                                           dict(defaults,
                                                **pattern.default_kwargs))
                            lookups.appendlist(name, lookup_list)
                    for namespace, (prefix, sub_pattern) in \
                            pattern.namespace_dict.items():
                        namespace_vals = (p_pattern + prefix, sub_pattern)
                        namespaces[namespace] = namespace_vals
                    for app_name, namespace_list in pattern.app_dict.items():
                        apps.setdefault(app_name, []).extend(namespace_list)
            else:
                bits = normalize(p_pattern)
                lookup_list = (bits, p_pattern, pattern.default_args)
                lookups.appendlist(pattern.callback, lookup_list)
                if pattern.name is not None:
                    lookup_list = (bits, p_pattern, pattern.default_args)
                    lookups.appendlist(pattern.name, lookup_list)
        self._reverse_dict = lookups
        self._namespace_dict = namespaces
        self._app_dict = apps

    def resolver_reverse(self, lookup_view, *args, **kwargs):
        return self._reverse_with_prefix(lookup_view, '', *args, **kwargs)

    def _reverse_with_prefix(self, lookup_view, _prefix, *args, **kwargs):
        if args and kwargs:
            raise ValueError("Don't mix *args and **kwargs in call to "
                             "reverse()!")
        try:
            lookup_view = urlresolvers.get_callable(lookup_view, True)
        except (ImportError, AttributeError), e:
            raise urlresolvers.NoReverseMatch("Error importing '%s': %s."
                                              % (lookup_view, e))
        possibilities = self.reverse_dict.getlist(lookup_view)
        prefix_norm, prefix_args = normalize(_prefix)[0]
        for possibility, pattern, defaults in possibilities:
            for result, params in possibility:
                if args:
                    if len(args) != len(params) + len(prefix_args):
                        continue
                    unicode_args = [force_unicode(val) for val in args]
                    candidate = (prefix_norm + result) \
                            % dict(zip(prefix_args + params, unicode_args))
                else:
                    if set(kwargs.keys() + defaults.keys()) != \
                            set(params + defaults.keys() + prefix_args):
                        continue
                    matches = True
                    for k, v in defaults.items():
                        if kwargs.get(k, v) != v:
                            matches = False
                            break
                    if not matches:
                        continue
                    unicode_kwargs = dict([(k, force_unicode(v)) for \
                            (k, v) in kwargs.items()])
                    candidate = (prefix_norm + result) % unicode_kwargs
                if re.search(u'^%s%s' % (_prefix, pattern),
                             candidate, re.UNICODE):
                    return candidate
        # lookup_view can be URL label, or dotted path, or callable, Any of
        # these can be passed in at the top, but callables are not friendly in
        # error messages.
        m = getattr(lookup_view, '__module__', None)
        n = getattr(lookup_view, '__name__', None)
        if m is not None and n is not None:
            lookup_view_s = "%s.%s" % (m, n)
        else:
            lookup_view_s = lookup_view
        raise urlresolvers.NoReverseMatch("Reverse for '%s' with "
                                          "arguments '%s' and keyword "
                                          "arguments '%s' not found."
                                          % (lookup_view_s, args, kwargs))

    def reverse(viewname, urlconf=None, args=None, kwargs=None, prefix=None,
                current_app=None):
        if urlconf is None:
            urlconf = urlresolvers.get_urlconf()
        resolver = urlresolvers.get_resolver(urlconf)
        args = args or []
        kwargs = kwargs or {}

        if prefix is None:
            prefix = urlresolvers.get_script_prefix()

        if not isinstance(viewname, basestring):
            view = viewname
        else:
            parts = viewname.split(':')
            parts.reverse()
            view = parts[0]
            path = parts[1:]

            resolved_path = []
            while path:
                ns = path.pop()

                # Lookup the name to see if it could be an app identifier
                try:
                    app_list = resolver.app_dict[ns]
                    # Yes! Path part matches an app in the current Resolver
                    if current_app and current_app in app_list:
                        # If we are reversing for a particular app,
                        # use that namespace
                        ns = current_app
                    elif ns not in app_list:
                        # The name isn't shared by one of the instances
                        # (i.e., the default) so just pick the first instance
                        # as the default.
                        ns = app_list[0]
                except KeyError:
                    pass

                try:
                    extra, resolver = resolver.namespace_dict[ns]
                    resolved_path.append(ns)
                    prefix = prefix + extra
                except KeyError, key:
                    if resolved_path:
                        raise urlresolvers.NoReverseMatch("%s is not a "
                                "registered namespace inside %s'"
                                % (key, ':'.join(resolved_path)))
                    else:
                        raise urlresolvers.NoReverseMatch("%s is not a "
                                                          "registered "
                                                          "namespace" % key)

        return iri_to_uri(resolver._reverse_with_prefix(view, prefix,
                                                        *args, **kwargs))

    urlresolvers.RegexURLResolver._populate = _populate
    urlresolvers.RegexURLResolver.reverse = resolver_reverse
    urlresolvers.RegexURLResolver._reverse_with_prefix = _reverse_with_prefix
    urlresolvers.reverse = reverse
