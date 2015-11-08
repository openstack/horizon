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

"""
Contains the core classes and functionality that makes Horizon what it is.
This module is considered internal, and should not be relied on directly.

Public APIs are made available through the :mod:`horizon` module and
the classes contained therein.
"""

import collections
import copy
import inspect
import logging
import os

from django.conf import settings
from django.conf.urls import include
from django.conf.urls import patterns
from django.conf.urls import url
from django.core.exceptions import ImproperlyConfigured  # noqa
from django.core.urlresolvers import reverse
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import empty
from django.utils.functional import SimpleLazyObject  # noqa
from django.utils.importlib import import_module  # noqa
from django.utils.module_loading import module_has_submodule  # noqa
from django.utils.translation import ugettext_lazy as _
import six

from horizon import conf
from horizon.decorators import _current_component  # noqa
from horizon.decorators import require_auth  # noqa
from horizon.decorators import require_perms  # noqa
from horizon import loaders


# Name of the panel group for panels to be displayed without a group.
DEFAULT_PANEL_GROUP = 'default'
LOG = logging.getLogger(__name__)


def _decorate_urlconf(urlpatterns, decorator, *args, **kwargs):
    for pattern in urlpatterns:
        if getattr(pattern, 'callback', None):
            pattern._callback = decorator(pattern.callback, *args, **kwargs)
        if getattr(pattern, 'url_patterns', []):
            _decorate_urlconf(pattern.url_patterns, decorator, *args, **kwargs)


# FIXME(lhcheng): We need to find a better way to cache the result.
# Rather than storing it in the session, we could leverage the Django
# session. Currently, this has been causing issue with cookie backend,
# adding 1600+ in the cookie size.
def access_cached(func):
    def inner(self, context):
        session = context['request'].session
        try:
            if session['allowed']['valid_for'] != session.get('token'):
                raise KeyError()
        except KeyError:
            session['allowed'] = {"valid_for": session.get('token')}

        key = "%s.%s" % (self.__class__.__module__, self.__class__.__name__)
        if key not in session['allowed']:
            session['allowed'][key] = func(self, context)
            session.modified = True
        return session['allowed'][key]
    return inner


class NotRegistered(Exception):
    pass


@python_2_unicode_compatible
class HorizonComponent(object):
    policy_rules = None

    def __init__(self):
        super(HorizonComponent, self).__init__()
        if not self.slug:
            raise ImproperlyConfigured('Every %s must have a slug.'
                                       % self.__class__)

    def __str__(self):
        name = getattr(self, 'name', u"Unnamed %s" % self.__class__.__name__)
        return name

    def _get_default_urlpatterns(self):
        package_string = '.'.join(self.__module__.split('.')[:-1])
        if getattr(self, 'urls', None):
            try:
                mod = import_module('.%s' % self.urls, package_string)
            except ImportError:
                mod = import_module(self.urls)
            urlpatterns = mod.urlpatterns
        else:
            # Try importing a urls.py from the dashboard package
            if module_has_submodule(import_module(package_string), 'urls'):
                urls_mod = import_module('.urls', package_string)
                urlpatterns = urls_mod.urlpatterns
            else:
                urlpatterns = patterns('')
        return urlpatterns

    # FIXME(lhcheng): Removed the access_cached decorator for now until
    # a better implementation has been figured out. This has been causing
    # issue with cookie backend, adding 1600+ in the cookie size.
    # @access_cached
    def can_access(self, context):
        """Return whether the user has role based access to this component.

        This method is not intended to be overridden.
        The result of the method is stored in per-session cache.
        """
        return self.allowed(context)

    def allowed(self, context):
        """Checks if the user is allowed to access this component.

        This method should be overridden to return the result of
        any policy checks required for the user to access this component
        when more complex checks are required.
        """
        return self._can_access(context['request'])

    def _can_access(self, request):
        policy_check = getattr(settings, "POLICY_CHECK_FUNCTION", None)

        # this check is an OR check rather than an AND check that is the
        # default in the policy engine, so calling each rule individually
        if policy_check and self.policy_rules:
            for rule in self.policy_rules:
                if policy_check((rule,), request):
                    return True
            return False

        # default to allowed
        return True


class Registry(object):
    def __init__(self):
        self._registry = {}
        if not getattr(self, '_registerable_class', None):
            raise ImproperlyConfigured('Subclasses of Registry must set a '
                                       '"_registerable_class" property.')

    def _register(self, cls):
        """Registers the given class.

        If the specified class is already registered then it is ignored.
        """
        if not inspect.isclass(cls):
            raise ValueError('Only classes may be registered.')
        elif not issubclass(cls, self._registerable_class):
            raise ValueError('Only %s classes or subclasses may be registered.'
                             % self._registerable_class.__name__)

        if cls not in self._registry:
            cls._registered_with = self
            self._registry[cls] = cls()

        return self._registry[cls]

    def _unregister(self, cls):
        """Unregisters the given class.

        If the specified class isn't registered, ``NotRegistered`` will
        be raised.
        """
        if not issubclass(cls, self._registerable_class):
            raise ValueError('Only %s classes or subclasses may be '
                             'unregistered.' % self._registerable_class)

        if cls not in self._registry.keys():
            raise NotRegistered('%s is not registered' % cls)

        del self._registry[cls]

        return True

    def _registered(self, cls):
        if inspect.isclass(cls) and issubclass(cls, self._registerable_class):
            found = self._registry.get(cls, None)
            if found:
                return found
        else:
            # Allow for fetching by slugs as well.
            for registered in self._registry.values():
                if registered.slug == cls:
                    return registered
        class_name = self._registerable_class.__name__
        if hasattr(self, "_registered_with"):
            parent = self._registered_with._registerable_class.__name__
            raise NotRegistered('%(type)s with slug "%(slug)s" is not '
                                'registered with %(parent)s "%(name)s".'
                                % {"type": class_name,
                                   "slug": cls,
                                   "parent": parent,
                                   "name": self.slug})
        else:
            slug = getattr(cls, "slug", cls)
            raise NotRegistered('%(type)s with slug "%(slug)s" is not '
                                'registered.' % {"type": class_name,
                                                 "slug": slug})


class Panel(HorizonComponent):
    """A base class for defining Horizon dashboard panels.

    All Horizon dashboard panels should extend from this class. It provides
    the appropriate hooks for automatically constructing URLconfs, and
    providing permission-based access control.

    .. attribute:: name

        The name of the panel. This will be displayed in the
        auto-generated navigation and various other places.
        Default: ``''``.

    .. attribute:: slug

        A unique "short name" for the panel. The slug is used as
        a component of the URL path for the panel. Default: ``''``.

    .. attribute:: permissions

        A list of permission names, all of which a user must possess in order
        to access any view associated with this panel. This attribute
        is combined cumulatively with any permissions required on the
        ``Dashboard`` class with which it is registered.

    .. attribute:: urls

        Path to a URLconf of views for this panel using dotted Python
        notation. If no value is specified, a file called ``urls.py``
        living in the same package as the ``panel.py`` file is used.
        Default: ``None``.

    .. attribute:: nav
    .. method:: nav(context)

        The ``nav`` attribute can be either boolean value or a callable
        which accepts a ``RequestContext`` object as a single argument
        to control whether or not this panel should appear in
        automatically-generated navigation. Default: ``True``.

    .. attribute:: index_url_name

        The ``name`` argument for the URL pattern which corresponds to
        the index view for this ``Panel``. This is the view that
        :meth:`.Panel.get_absolute_url` will attempt to reverse.

    .. staticmethod:: can_register

        This optional static method can be used to specify conditions that
        need to be satisfied to load this panel. Unlike ``permissions`` and
        ``allowed`` this method is intended to handle settings based
        conditions rather than user based permission and policy checks.
        The return value is boolean. If the method returns ``True``, then the
        panel will be registered and available to user (if ``permissions`` and
        ``allowed`` runtime checks are also satisfied). If the method returns
        ``False``, then the panel will not be registered and will not be
        available via normal navigation or direct URL access.
    """
    name = ''
    slug = ''
    urls = None
    nav = True
    index_url_name = "index"

    def __repr__(self):
        return "<Panel: %s>" % self.slug

    def get_absolute_url(self):
        """Returns the default URL for this panel.

        The default URL is defined as the URL pattern with ``name="index"`` in
        the URLconf for this panel.
        """
        try:
            return reverse('horizon:%s:%s:%s' % (self._registered_with.slug,
                                                 self.slug,
                                                 self.index_url_name))
        except Exception as exc:
            # Logging here since this will often be called in a template
            # where the exception would be hidden.
            LOG.info("Error reversing absolute URL for %s: %s" % (self, exc))
            raise

    @property
    def _decorated_urls(self):
        urlpatterns = self._get_default_urlpatterns()

        # Apply access controls to all views in the patterns
        permissions = getattr(self, 'permissions', [])
        _decorate_urlconf(urlpatterns, require_perms, permissions)
        _decorate_urlconf(urlpatterns, _current_component, panel=self)

        # Return the three arguments to django.conf.urls.include
        return urlpatterns, self.slug, self.slug


@six.python_2_unicode_compatible
class PanelGroup(object):
    """A container for a set of :class:`~horizon.Panel` classes.

    When iterated, it will yield each of the ``Panel`` instances it
    contains.

    .. attribute:: slug

        A unique string to identify this panel group. Required.

    .. attribute:: name

        A user-friendly name which will be used as the group heading in
        places such as the navigation. Default: ``None``.

    .. attribute:: panels

        A list of panel module names which should be contained within this
        grouping.
    """
    def __init__(self, dashboard, slug=None, name=None, panels=None):
        self.dashboard = dashboard
        self.slug = slug or getattr(self, "slug", DEFAULT_PANEL_GROUP)
        self.name = name or getattr(self, "name", None)
        # Our panels must be mutable so it can be extended by others.
        self.panels = list(panels or getattr(self, "panels", []))

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.slug)

    def __str__(self):
        return self.name

    def __iter__(self):
        panel_instances = []
        for name in self.panels:
            try:
                panel_instances.append(self.dashboard.get_panel(name))
            except NotRegistered as e:
                LOG.debug(e)
        return iter(panel_instances)


class Dashboard(Registry, HorizonComponent):
    """A base class for defining Horizon dashboards.

    All Horizon dashboards should extend from this base class. It provides the
    appropriate hooks for automatic discovery of :class:`~horizon.Panel`
    modules, automatically constructing URLconfs, and providing
    permission-based access control.

    .. attribute:: name

        The name of the dashboard. This will be displayed in the
        auto-generated navigation and various other places.
        Default: ``''``.

    .. attribute:: slug

        A unique "short name" for the dashboard. The slug is used as
        a component of the URL path for the dashboard. Default: ``''``.

    .. attribute:: panels

        The ``panels`` attribute can be either a flat list containing the name
        of each panel **module**  which should be loaded as part of this
        dashboard, or a list of :class:`~horizon.PanelGroup` classes which
        define groups of panels as in the following example::

            class SystemPanels(horizon.PanelGroup):
                slug = "syspanel"
                name = _("System")
                panels = ('overview', 'instances', ...)

            class Syspanel(horizon.Dashboard):
                panels = (SystemPanels,)

        Automatically generated navigation will use the order of the
        modules in this attribute.

        Default: ``[]``.

        .. warning::

            The values for this attribute should not correspond to the
            :attr:`~.Panel.name` attributes of the ``Panel`` classes.
            They should be the names of the Python modules in which the
            ``panel.py`` files live. This is used for the automatic
            loading and registration of ``Panel`` classes much like
            Django's ``ModelAdmin`` machinery.

            Panel modules must be listed in ``panels`` in order to be
            discovered by the automatic registration mechanism.

    .. attribute:: default_panel

        The name of the panel which should be treated as the default
        panel for the dashboard, i.e. when you visit the root URL
        for this dashboard, that's the panel that is displayed.
        Default: ``None``.

    .. attribute:: permissions

        A list of permission names, all of which a user must possess in order
        to access any panel registered with this dashboard. This attribute
        is combined cumulatively with any permissions required on individual
        :class:`~horizon.Panel` classes.

    .. attribute:: urls

        Optional path to a URLconf of additional views for this dashboard
        which are not connected to specific panels. Default: ``None``.

    .. attribute:: nav
    .. method:: nav(context)

        The ``nav`` attribute can be either boolean value or a callable
        which accepts a ``RequestContext`` object as a single argument
        to control whether or not this dashboard should appear in
        automatically-generated navigation. Default: ``True``.

    .. attribute:: public

        Boolean value to determine whether this dashboard can be viewed
        without being logged in. Defaults to ``False``.

    """
    _registerable_class = Panel
    name = ''
    slug = ''
    urls = None
    panels = []
    default_panel = None
    nav = True
    public = False

    def __repr__(self):
        return "<Dashboard: %s>" % self.slug

    def __init__(self, *args, **kwargs):
        super(Dashboard, self).__init__(*args, **kwargs)
        self._panel_groups = None

    def get_panel(self, panel):
        """Returns the specified :class:`~horizon.Panel` instance registered
        with this dashboard.
        """
        return self._registered(panel)

    def get_panels(self):
        """Returns the :class:`~horizon.Panel` instances registered with this
        dashboard in order, without any panel groupings.
        """
        all_panels = []
        panel_groups = self.get_panel_groups()
        for panel_group in panel_groups.values():
            all_panels.extend(panel_group)
        return all_panels

    def get_panel_group(self, slug):
        """Returns the specified :class:~horizon.PanelGroup
        or None if not registered
        """
        return self._panel_groups.get(slug)

    def get_panel_groups(self):
        registered = copy.copy(self._registry)
        panel_groups = []

        # Gather our known panels
        if self._panel_groups is not None:
            for panel_group in self._panel_groups.values():
                for panel in panel_group:
                    registered.pop(panel.__class__)
                panel_groups.append((panel_group.slug, panel_group))

        # Deal with leftovers (such as add-on registrations)
        if len(registered):
            slugs = [panel.slug for panel in registered.values()]
            new_group = PanelGroup(self,
                                   slug="other",
                                   name=_("Other"),
                                   panels=slugs)
            panel_groups.append((new_group.slug, new_group))
        return collections.OrderedDict(panel_groups)

    def get_absolute_url(self):
        """Returns the default URL for this dashboard.

        The default URL is defined as the URL pattern with ``name="index"``
        in the URLconf for the :class:`~horizon.Panel` specified by
        :attr:`~horizon.Dashboard.default_panel`.
        """
        try:
            return self._registered(self.default_panel).get_absolute_url()
        except Exception:
            # Logging here since this will often be called in a template
            # where the exception would be hidden.
            LOG.exception("Error reversing absolute URL for %s." % self)
            raise

    @property
    def _decorated_urls(self):
        urlpatterns = self._get_default_urlpatterns()

        default_panel = None

        # Add in each panel's views except for the default view.
        for panel in self._registry.values():
            if panel.slug == self.default_panel:
                default_panel = panel
                continue
            url_slug = panel.slug.replace('.', '/')
            urlpatterns += patterns('',
                                    url(r'^%s/' % url_slug,
                                        include(panel._decorated_urls)))
        # Now the default view, which should come last
        if not default_panel:
            raise NotRegistered('The default panel "%s" is not registered.'
                                % self.default_panel)
        urlpatterns += patterns('',
                                url(r'',
                                    include(default_panel._decorated_urls)))

        # Require login if not public.
        if not self.public:
            _decorate_urlconf(urlpatterns, require_auth)
        # Apply access controls to all views in the patterns
        permissions = getattr(self, 'permissions', [])
        _decorate_urlconf(urlpatterns, require_perms, permissions)
        _decorate_urlconf(urlpatterns, _current_component, dashboard=self)

        # Return the three arguments to django.conf.urls.include
        return urlpatterns, self.slug, self.slug

    def _autodiscover(self):
        """Discovers panels to register from the current dashboard module."""
        if getattr(self, "_autodiscover_complete", False):
            return

        panels_to_discover = []
        panel_groups = []
        # If we have a flat iterable of panel names, wrap it again so
        # we have a consistent structure for the next step.
        if all([isinstance(i, six.string_types) for i in self.panels]):
            self.panels = [self.panels]

        # Now iterate our panel sets.
        default_created = False
        for panel_set in self.panels:
            # Instantiate PanelGroup classes.
            if not isinstance(panel_set, collections.Iterable) and \
                    issubclass(panel_set, PanelGroup):
                panel_group = panel_set(self)
            # Check for nested tuples, and convert them to PanelGroups
            elif not isinstance(panel_set, PanelGroup):
                panel_group = PanelGroup(self, panels=panel_set)

            # Put our results into their appropriate places
            panels_to_discover.extend(panel_group.panels)
            panel_groups.append((panel_group.slug, panel_group))
            if panel_group.slug == DEFAULT_PANEL_GROUP:
                default_created = True

        # Plugin panels can be added to a default panel group. Make sure such a
        # default group exists.
        if not default_created:
            default_group = PanelGroup(self)
            panel_groups.insert(0, (default_group.slug, default_group))
        self._panel_groups = collections.OrderedDict(panel_groups)

        # Do the actual discovery
        package = '.'.join(self.__module__.split('.')[:-1])
        mod = import_module(package)
        for panel in panels_to_discover:
            try:
                before_import_registry = copy.copy(self._registry)
                import_module('.%s.panel' % panel, package)
            except Exception:
                self._registry = before_import_registry
                if module_has_submodule(mod, panel):
                    raise
        self._autodiscover_complete = True

    @classmethod
    def register(cls, panel):
        """Registers a :class:`~horizon.Panel` with this dashboard."""
        panel_class = Horizon.register_panel(cls, panel)
        # Support template loading from panel template directories.
        panel_mod = import_module(panel.__module__)
        panel_dir = os.path.dirname(panel_mod.__file__)
        template_dir = os.path.join(panel_dir, "templates")
        if os.path.exists(template_dir):
            key = os.path.join(cls.slug, panel.slug)
            loaders.panel_template_dirs[key] = template_dir
        return panel_class

    @classmethod
    def unregister(cls, panel):
        """Unregisters a :class:`~horizon.Panel` from this dashboard."""
        success = Horizon.unregister_panel(cls, panel)
        if success:
            # Remove the panel's template directory.
            key = os.path.join(cls.slug, panel.slug)
            if key in loaders.panel_template_dirs:
                del loaders.panel_template_dirs[key]
        return success

    def allowed(self, context):
        """Checks for role based access for this dashboard.

        Checks for access to any panels in the dashboard and of the the
        dashboard itself.

        This method should be overridden to return the result of
        any policy checks required for the user to access this dashboard
        when more complex checks are required.
        """

        # if the dashboard has policy rules, honor those above individual
        # panels
        if not self._can_access(context['request']):
            return False

        # check if access is allowed to a single panel,
        # the default for each panel is True
        for panel in self.get_panels():
            if panel.can_access(context):
                return True

        return False


class Workflow(object):
    pass


class LazyURLPattern(SimpleLazyObject):
    def __iter__(self):
        if self._wrapped is empty:
            self._setup()
        return iter(self._wrapped)

    def __reversed__(self):
        if self._wrapped is empty:
            self._setup()
        return reversed(self._wrapped)

    def __len__(self):
        if self._wrapped is empty:
            self._setup()
        return len(self._wrapped)

    def __getitem__(self, idx):
        if self._wrapped is empty:
            self._setup()
        return self._wrapped[idx]


class Site(Registry, HorizonComponent):
    """The overarching class which encompasses all dashboards and panels."""

    # Required for registry
    _registerable_class = Dashboard

    name = "Horizon"
    namespace = 'horizon'
    slug = 'horizon'
    urls = 'horizon.site_urls'

    def __repr__(self):
        return u"<Site: %s>" % self.slug

    @property
    def _conf(self):
        return conf.HORIZON_CONFIG

    @property
    def dashboards(self):
        return self._conf['dashboards']

    @property
    def default_dashboard(self):
        return self._conf['default_dashboard']

    def register(self, dashboard):
        """Registers a :class:`~horizon.Dashboard` with Horizon."""
        return self._register(dashboard)

    def unregister(self, dashboard):
        """Unregisters a :class:`~horizon.Dashboard` from Horizon."""
        return self._unregister(dashboard)

    def registered(self, dashboard):
        return self._registered(dashboard)

    def register_panel(self, dashboard, panel):
        dash_instance = self.registered(dashboard)
        return dash_instance._register(panel)

    def unregister_panel(self, dashboard, panel):
        dash_instance = self.registered(dashboard)
        if not dash_instance:
            raise NotRegistered("The dashboard %s is not registered."
                                % dashboard)
        return dash_instance._unregister(panel)

    def get_dashboard(self, dashboard):
        """Returns the specified :class:`~horizon.Dashboard` instance."""
        return self._registered(dashboard)

    def get_dashboards(self):
        """Returns an ordered tuple of :class:`~horizon.Dashboard` modules.

        Orders dashboards according to the ``"dashboards"`` key in
        ``HORIZON_CONFIG`` or else returns all registered dashboards
        in alphabetical order.

        Any remaining :class:`~horizon.Dashboard` classes registered with
        Horizon but not listed in ``HORIZON_CONFIG['dashboards']``
        will be appended to the end of the list alphabetically.
        """
        if self.dashboards:
            registered = copy.copy(self._registry)
            dashboards = []
            for item in self.dashboards:
                dashboard = self._registered(item)
                dashboards.append(dashboard)
                registered.pop(dashboard.__class__)
            if len(registered):
                extra = sorted(registered.values())
                dashboards.extend(extra)
            return dashboards
        else:
            return sorted(self._registry.values())

    def get_default_dashboard(self):
        """Returns the default :class:`~horizon.Dashboard` instance.

        If ``"default_dashboard"`` is specified in ``HORIZON_CONFIG``
        then that dashboard will be returned. If not, the first dashboard
        returned by :func:`~horizon.get_dashboards` will be returned.
        """
        if self.default_dashboard:
            return self._registered(self.default_dashboard)
        elif len(self._registry):
            return self.get_dashboards()[0]
        else:
            raise NotRegistered("No dashboard modules have been registered.")

    def get_user_home(self, user):
        """Returns the default URL for a particular user.

        This method can be used to customize where a user is sent when
        they log in, etc. By default it returns the value of
        :meth:`get_absolute_url`.

        An alternative function can be supplied to customize this behavior
        by specifying a either a URL or a function which returns a URL via
        the ``"user_home"`` key in ``HORIZON_CONFIG``. Each of these
        would be valid::

            {"user_home": "/home",}  # A URL
            {"user_home": "my_module.get_user_home",}  # Path to a function
            {"user_home": lambda user: "/" + user.name,}  # A function
            {"user_home": None,}  # Will always return the default dashboard

        This can be useful if the default dashboard may not be accessible
        to all users. When user_home is missing from HORIZON_CONFIG,
        it will default to the settings.LOGIN_REDIRECT_URL value.
        """
        user_home = self._conf['user_home']
        if user_home:
            if callable(user_home):
                return user_home(user)
            elif isinstance(user_home, six.string_types):
                # Assume we've got a URL if there's a slash in it
                if '/' in user_home:
                    return user_home
                else:
                    mod, func = user_home.rsplit(".", 1)
                    return getattr(import_module(mod), func)(user)
            # If it's not callable and not a string, it's wrong.
            raise ValueError('The user_home setting must be either a string '
                             'or a callable object (e.g. a function).')
        else:
            return self.get_absolute_url()

    def get_absolute_url(self):
        """Returns the default URL for Horizon's URLconf.

        The default URL is determined by calling
        :meth:`~horizon.Dashboard.get_absolute_url`
        on the :class:`~horizon.Dashboard` instance returned by
        :meth:`~horizon.get_default_dashboard`.
        """
        return self.get_default_dashboard().get_absolute_url()

    @property
    def _lazy_urls(self):
        """Lazy loading for URL patterns.

        This method avoids problems associated with attempting to evaluate
        the URLconf before the settings module has been loaded.
        """
        def url_patterns():
            return self._urls()[0]

        return LazyURLPattern(url_patterns), self.namespace, self.slug

    def _urls(self):
        """Constructs the URLconf for Horizon from registered Dashboards."""
        urlpatterns = self._get_default_urlpatterns()
        self._autodiscover()

        # Discover each dashboard's panels.
        for dash in self._registry.values():
            dash._autodiscover()

        # Load the plugin-based panel configuration
        self._load_panel_customization()

        # Allow for override modules
        if self._conf.get("customization_module", None):
            customization_module = self._conf["customization_module"]
            bits = customization_module.split('.')
            mod_name = bits.pop()
            package = '.'.join(bits)
            mod = import_module(package)
            try:
                before_import_registry = copy.copy(self._registry)
                import_module('%s.%s' % (package, mod_name))
            except Exception:
                self._registry = before_import_registry
                if module_has_submodule(mod, mod_name):
                    raise

        # Compile the dynamic urlconf.
        for dash in self._registry.values():
            urlpatterns += patterns('',
                                    url(r'^%s/' % dash.slug,
                                        include(dash._decorated_urls)))

        # Return the three arguments to django.conf.urls.include
        return urlpatterns, self.namespace, self.slug

    def _autodiscover(self):
        """Discovers modules to register from ``settings.INSTALLED_APPS``.

        This makes sure that the appropriate modules get imported to register
        themselves with Horizon.
        """
        if not getattr(self, '_registerable_class', None):
            raise ImproperlyConfigured('You must set a '
                                       '"_registerable_class" property '
                                       'in order to use autodiscovery.')
        # Discover both dashboards and panels, in that order
        for mod_name in ('dashboard', 'panel'):
            for app in settings.INSTALLED_APPS:
                mod = import_module(app)
                try:
                    before_import_registry = copy.copy(self._registry)
                    import_module('%s.%s' % (app, mod_name))
                except Exception:
                    self._registry = before_import_registry
                    if module_has_submodule(mod, mod_name):
                        raise

    def _load_panel_customization(self):
        """Applies the plugin-based panel configurations.

        This method parses the panel customization from the ``HORIZON_CONFIG``
        and make changes to the dashboard accordingly.

        It supports adding, removing and setting default panels on the
        dashboard. It also support registering a panel group.
        """
        panel_customization = self._conf.get("panel_customization", [])

        # Process all the panel groups first so that they exist before panels
        # are added to them and Dashboard._autodiscover() doesn't wipe out any
        # panels previously added when its panel groups are instantiated.
        panel_configs = []
        for config in panel_customization:
            if config.get('PANEL'):
                panel_configs.append(config)
            elif config.get('PANEL_GROUP'):
                self._process_panel_group_configuration(config)
            else:
                LOG.warning("Skipping %s because it doesn't have PANEL or "
                            "PANEL_GROUP defined.", config.__name__)
        # Now process the panels.
        for config in panel_configs:
            self._process_panel_configuration(config)

    def _process_panel_configuration(self, config):
        """Add, remove and set default panels on the dashboard."""
        try:
            dashboard = config.get('PANEL_DASHBOARD')
            if not dashboard:
                LOG.warning("Skipping %s because it doesn't have "
                            "PANEL_DASHBOARD defined.", config.__name__)
                return
            panel_slug = config.get('PANEL')
            dashboard_cls = self.get_dashboard(dashboard)
            panel_group = config.get('PANEL_GROUP')
            default_panel = config.get('DEFAULT_PANEL')

            # Set the default panel
            if default_panel:
                dashboard_cls.default_panel = default_panel

            # Remove the panel
            if config.get('REMOVE_PANEL', False):
                for panel in dashboard_cls.get_panels():
                    if panel_slug == panel.slug:
                        dashboard_cls.unregister(panel.__class__)
            elif config.get('ADD_PANEL', None):
                # Add the panel to the dashboard
                panel_path = config['ADD_PANEL']
                mod_path, panel_cls = panel_path.rsplit(".", 1)
                try:
                    mod = import_module(mod_path)
                except ImportError:
                    LOG.warning("Could not load panel: %s", mod_path)
                    return
                panel = getattr(mod, panel_cls)
                # test is can_register method is present and call method if
                # it is to determine if the panel should be loaded
                if hasattr(panel, 'can_register') and \
                   callable(getattr(panel, 'can_register')):
                    if not panel.can_register():
                        LOG.debug("Load condition failed for panel: %(panel)s",
                                  {'panel': panel_slug})
                        return
                dashboard_cls.register(panel)
                if panel_group:
                    dashboard_cls.get_panel_group(panel_group).\
                        panels.append(panel.slug)
                else:
                    panels = list(dashboard_cls.panels)
                    panels.append(panel)
                    dashboard_cls.panels = tuple(panels)
        except Exception as e:
            LOG.warning('Could not process panel %(panel)s: %(exc)s',
                        {'panel': panel_slug, 'exc': e})

    def _process_panel_group_configuration(self, config):
        """Adds a panel group to the dashboard."""
        panel_group_slug = config.get('PANEL_GROUP')
        try:
            dashboard = config.get('PANEL_GROUP_DASHBOARD')
            if not dashboard:
                LOG.warning("Skipping %s because it doesn't have "
                            "PANEL_GROUP_DASHBOARD defined.", config.__name__)
                return
            dashboard_cls = self.get_dashboard(dashboard)

            panel_group_name = config.get('PANEL_GROUP_NAME')
            if not panel_group_name:
                LOG.warning("Skipping %s because it doesn't have "
                            "PANEL_GROUP_NAME defined.", config.__name__)
                return
            # Create the panel group class
            panel_group = type(panel_group_slug,
                               (PanelGroup, ),
                               {'slug': panel_group_slug,
                                'name': panel_group_name,
                                'panels': []},)
            # Add the panel group to dashboard
            panels = list(dashboard_cls.panels)
            panels.append(panel_group)
            dashboard_cls.panels = tuple(panels)
            # Trigger the autodiscovery to completely load the new panel group
            dashboard_cls._autodiscover_complete = False
            dashboard_cls._autodiscover()
        except Exception as e:
            LOG.warning('Could not process panel group %(panel_group)s: '
                        '%(exc)s',
                        {'panel_group': panel_group_slug, 'exc': e})


class HorizonSite(Site):
    """A singleton implementation of Site such that all dealings with horizon
    get the same instance no matter what. There can be only one.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Site, cls).__new__(cls, *args, **kwargs)
        return cls._instance


# The one true Horizon
Horizon = HorizonSite()
