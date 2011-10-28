"""
Backports the ``register.assignment_tag`` functionality from Django 1.4 to
Django 1.3.

This code is almost entirely reproduced from
https://code.djangoproject.com/browser/django/trunk/django/template/base.py
and is the work of Django's authors:
https://code.djangoproject.com/browser/django/trunk/AUTHORS

It is licensed under Django's BSD license, available here:
https://code.djangoproject.com/browser/django/trunk/LICENSE

To use, simply import this code in your project prior to using the
``register.assignment_tag``. In general, the top of your template tag
python file would be a good place for the import.
"""
import re
from inspect import getargspec

from django.template import TemplateSyntaxError
from django.template.base import Node, Library


if not hasattr(Library, 'assignment_tag'):
    # Regex for token keyword arguments
    kwarg_re = re.compile(r"(?:(\w+)=)?(.+)")

    def token_kwargs(bits, parser, support_legacy=False):
        """
        A utility method for parsing token keyword arguments.

        :param bits: A list containing remainder of the token (split by spaces)
            that is to be checked for arguments. Valid arguments will be removed
            from this list.

        :param support_legacy: If set to true ``True``, the legacy format
            ``1 as foo`` will be accepted. Otherwise, only the standard ``foo=1``
            format is allowed.

        :returns: A dictionary of the arguments retrieved from the ``bits`` token
            list.

        There is no requirement for all remaining token ``bits`` to be keyword
        arguments, so the dictionary will be returned as soon as an invalid
        argument format is reached.
        """
        if not bits:
            return {}
        match = kwarg_re.match(bits[0])
        kwarg_format = match and match.group(1)
        if not kwarg_format:
            if not support_legacy:
                return {}
            if len(bits) < 3 or bits[1] != 'as':
                return {}

        kwargs = {}
        while bits:
            if kwarg_format:
                match = kwarg_re.match(bits[0])
                if not match or not match.group(1):
                    return kwargs
                key, value = match.groups()
                del bits[:1]
            else:
                if len(bits) < 3 or bits[1] != 'as':
                    return kwargs
                key, value = bits[2], bits[0]
                del bits[:3]
            kwargs[key] = parser.compile_filter(value)
            if bits and not kwarg_format:
                if bits[0] != 'and':
                    return kwargs
                del bits[:1]
        return kwargs

    def parse_bits(parser, bits, params, varargs, varkw, defaults,
               takes_context, name):
        """
        Parses bits for template tag helpers (simple_tag, include_tag and
        assignment_tag), in particular by detecting syntax errors and by
        extracting positional and keyword arguments.
        """
        if takes_context:
            if params[0] == 'context':
                params = params[1:]
            else:
                raise TemplateSyntaxError(
                    "'%s' is decorated with takes_context=True so it must "
                    "have a first argument of 'context'" % name)
        args = []
        kwargs = {}
        unhandled_params = list(params)
        for bit in bits:
            # First we try to extract a potential kwarg from the bit
            kwarg = token_kwargs([bit], parser)
            if kwarg:
                # The kwarg was successfully extracted
                param, value = kwarg.items()[0]
                if param not in params and varkw is None:
                    # An unexpected keyword argument was supplied
                    raise TemplateSyntaxError(
                        "'%s' received unexpected keyword argument '%s'" %
                        (name, param))
                elif param in kwargs:
                    # The keyword argument has already been supplied once
                    raise TemplateSyntaxError(
                        "'%s' received multiple values for keyword argument '%s'" %
                        (name, param))
                else:
                    # All good, record the keyword argument
                    kwargs[str(param)] = value
                    if param in unhandled_params:
                        # If using the keyword syntax for a positional arg, then
                        # consume it.
                        unhandled_params.remove(param)
            else:
                if kwargs:
                    raise TemplateSyntaxError(
                        "'%s' received some positional argument(s) after some "
                        "keyword argument(s)" % name)
                else:
                    # Record the positional argument
                    args.append(parser.compile_filter(bit))
                    try:
                        # Consume from the list of expected positional arguments
                        unhandled_params.pop(0)
                    except IndexError:
                        if varargs is None:
                            raise TemplateSyntaxError(
                                "'%s' received too many positional arguments" %
                                name)
        if defaults is not None:
            # Consider the last n params handled, where n is the
            # number of defaults.
            unhandled_params = unhandled_params[:-len(defaults)]
        if unhandled_params:
            # Some positional arguments were not supplied
            raise TemplateSyntaxError(
                u"'%s' did not receive value(s) for the argument(s): %s" %
                (name, u", ".join([u"'%s'" % p for p in unhandled_params])))
        return args, kwargs


    class TagHelperNode(Node):
        """
        Base class for tag helper nodes such as SimpleNode, InclusionNode and
        AssignmentNode. Manages the positional and keyword arguments to be passed
        to the decorated function.
        """

        def __init__(self, takes_context, args, kwargs):
            self.takes_context = takes_context
            self.args = args
            self.kwargs = kwargs

        def get_resolved_arguments(self, context):
            resolved_args = [var.resolve(context) for var in self.args]
            if self.takes_context:
                resolved_args = [context] + resolved_args
            resolved_kwargs = dict((k, v.resolve(context))
                                    for k, v in self.kwargs.items())
            return resolved_args, resolved_kwargs


    def assignment_tag(self, func=None, takes_context=None, name=None):
            def dec(func):
                params, varargs, varkw, defaults = getargspec(func)

                class AssignmentNode(TagHelperNode):
                    def __init__(self, takes_context, args, kwargs, target_var):
                        super(AssignmentNode, self).__init__(takes_context, args, kwargs)
                        self.target_var = target_var

                    def render(self, context):
                        resolved_args, resolved_kwargs = self.get_resolved_arguments(context)
                        context[self.target_var] = func(*resolved_args, **resolved_kwargs)
                        return ''

                function_name = (name or
                    getattr(func, '_decorated_function', func).__name__)

                def compile_func(parser, token):
                    bits = token.split_contents()[1:]
                    if len(bits) < 2 or bits[-2] != 'as':
                        raise TemplateSyntaxError(
                            "'%s' tag takes at least 2 arguments and the "
                            "second last argument must be 'as'" % function_name)
                    target_var = bits[-1]
                    bits = bits[:-2]
                    args, kwargs = parse_bits(parser, bits, params,
                        varargs, varkw, defaults, takes_context, function_name)
                    return AssignmentNode(takes_context, args, kwargs, target_var)

                compile_func.__doc__ = func.__doc__
                self.tag(function_name, compile_func)
                return func

            if func is None:
                # @register.assignment_tag(...)
                return dec
            elif callable(func):
                # @register.assignment_tag
                return dec(func)
            else:
                raise TemplateSyntaxError("Invalid arguments provided to assignment_tag")


    Library.assignment_tag = assignment_tag
