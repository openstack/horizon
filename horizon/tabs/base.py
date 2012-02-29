# vim: tabstop=4 shiftwidth=4 softtabstop=4

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

from django.template import TemplateSyntaxError
from django.template.loader import render_to_string
from django.utils.datastructures import SortedDict

from horizon.utils import html

SEPARATOR = "__"
CSS_TAB_GROUP_CLASSES = ["nav", "nav-tabs", "ajax-tabs"]
CSS_ACTIVE_TAB_CLASSES = ["active"]
CSS_DISABLED_TAB_CLASSES = ["disabled"]


class TabGroup(html.HTMLElement):
    """
    A container class which knows how to manage and render
    :class:`~horizon.tabs.Tab` objects.

    .. attribute:: slug

        The URL slug and pseudo-unique identifier for this tab group.

    .. attribute:: template_name

        The name of the template which will be used to render this tab group.
        Default: ``"horizon/common/_tab_group.html"``

    .. attribute:: param_name

        The name of the GET request parameter which will be used when
        requesting specific tab data. Default: ``tab``.

    .. attribute:: classes

        A list of CSS classes which should be displayed on this tab group.

    .. attribute:: attrs

        A dictionary of HTML attributes which should be rendered into the
        markup for this tab group.

    .. attribute:: selected

        Read-only property which is set to the instance of the
        currently-selected tab if there is one, otherwise ``None``.

    .. attribute:: active

        Read-only property which is set to the value of the current active tab.
        This may not be the same as the value of ``selected`` if no
        specific tab was requested via the ``GET`` parameter.
    """
    slug = None
    template_name = "horizon/common/_tab_group.html"
    param_name = 'tab'
    _selected = None
    _active = None

    @property
    def selected(self):
        return self._selected

    @property
    def active(self):
        return self._active

    def __init__(self, request, **kwargs):
        super(TabGroup, self).__init__()
        if not hasattr(self, "tabs"):
            raise NotImplementedError('%s must declare a "tabs" attribute.'
                                      % self.__class__)
        self.request = request
        self.kwargs = kwargs
        tab_instances = []
        for tab in self.tabs:
            tab_instances.append((tab.slug, tab(self, request)))
        self._tabs = SortedDict(tab_instances)
        if not self._set_active_tab():
            self.tabs_not_available()

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.slug)

    def get_id(self):
        """
        Returns the id for this tab group. Defaults to the value of the tab
        group's :attr:`horizon.tabs.Tab.slug`.
        """
        return self.slug

    def get_default_classes(self):
        """
        Returns a list of the default classes for the tab group. Defaults to
        ``["nav", "nav-tabs", "ajax-tabs"]``.
        """
        default_classes = super(TabGroup, self).get_default_classes()
        default_classes.extend(CSS_TAB_GROUP_CLASSES)
        return default_classes

    def tabs_not_available(self):
        """
        In the event that no tabs are either allowed or enabled, this method
        is the fallback handler. By default it's a no-op, but it exists
        to make redirecting or raising exceptions possible for subclasses.
        """
        pass

    def _set_active_tab(self):
        marked_active = None

        # See if we have a selected tab via the GET parameter.
        tab = self.get_selected_tab()
        if tab:
            tab._active = True
            self._active = tab
            marked_active = tab

        # Iterate through to mark them all accordingly.
        for tab in self._tabs.values():
            if tab._allowed and tab._enabled and not marked_active:
                tab._active = True
                self._active = tab
                marked_active = True
            elif tab == marked_active:
                continue
            else:
                tab._active = False

        return marked_active

    def render(self):
        """ Renders the HTML output for this tab group. """
        return render_to_string(self.template_name, {"tab_group": self})

    def get_tabs(self):
        """ Returns a list of the allowed tabs for this tab group. """
        return filter(lambda tab: tab._allowed, self._tabs.values())

    def get_tab(self, tab_name, allow_disabled=False):
        """ Returns a specific tab from this tab group.

        If the tab is not allowed or not enabled this method returns ``None``.

        If the tab is disabled but you wish to return it anyway, you can pass
        ``True`` to the allow_disabled argument.
        """
        tab = self._tabs.get(tab_name, None)
        if tab and tab._allowed and (tab._enabled or allow_disabled):
            return tab
        return None

    def get_selected_tab(self):
        """ Returns the tab specific by the GET request parameter.

        In the event that there is no GET request parameter, the value
        of the query parameter is invalid, or the tab is not allowed/enabled,
        the return value of this function is None.
        """
        selected = self.request.GET.get(self.param_name, None)
        if selected:
            tab_group, tab_name = selected.split(SEPARATOR)
            if tab_group == self.get_id():
                self._selected = self.get_tab(tab_name)
        return self._selected


class Tab(html.HTMLElement):
    """
    A reusable interface for constructing a tab within a
    :class:`~horizon.tabs.TabGroup`.

    .. attribute:: name

        The display name for the tab which will be rendered as the text for
        the tab element in the HTML. Required.

    .. attribute:: slug

        The URL slug and id attribute for the tab. This should be unique for
        a given tab group. Required.

    .. attribute:: preload

        Determines whether the contents of the tab should be rendered into
        the page's HTML when the tab group is rendered, or whether it should
        be loaded dynamically when the tab is selected. Default: ``True``.

    .. attribute:: classes

        A list of CSS classes which should be displayed on this tab.

    .. attribute:: attrs

        A dictionary of HTML attributes which should be rendered into the
        markup for this tab.

    .. attribute:: load

        Read-only access to determine whether or not this tab's data should
        be loaded immediately.
    """
    name = None
    slug = None
    preload = True
    _active = None

    def __init__(self, tab_group, request):
        super(Tab, self).__init__()
        # Priority: constructor, class-defined, fallback
        if not self.name:
            raise ValueError("%s must have a name." % self.__class__.__name__)
        self.name = unicode(self.name)  # Force unicode.
        if not self.slug:
            raise ValueError("%s must have a slug." % self.__class__.__name__)
        self.request = request
        self.tab_group = tab_group
        self._allowed = self.allowed(request)
        self._enabled = self.enabled(request)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.slug)

    def is_active(self):
        """ Method to access whether or not this tab is the active tab. """
        if self._active is None:
            self.tab_group._set_active_tab()
        return self._active

    @property
    def load(self):
        load_preloaded = self.preload or self.is_active()
        return load_preloaded and self._allowed and self._enabled

    def render(self):
        """
        Renders the tab to HTML using the :meth:`~horizon.tabs.Tab.get_data`
        method and the :meth:`~horizon.tabs.Tab.get_template_name` method.

        If :attr:`~horizon.tabs.Tab.preload` is ``False`` and ``force_load``
        is not ``True``, or
        either :meth:`~horizon.tabs.Tab.allowed` or
        :meth:`~horizon.tabs.Tab.enabled` returns ``False`` this method will
        return an empty string.
        """
        if not self.load:
            return ''
        try:
            context = self.get_context_data(self.request)
        except Exception as exc:
            raise TemplateSyntaxError(exc)
        return render_to_string(self.get_template_name(self.request), context)

    def get_id(self):
        """
        Returns the id for this tab. Defaults to
        ``"{{ tab_group.slug }}__{{ tab.slug }}"``.
        """
        return SEPARATOR.join([self.tab_group.slug, self.slug])

    def get_default_classes(self):
        """
        Returns a list of the default classes for the tab. Defaults to
        and empty list (``[]``), however additional classes may be added
        depending on the state of the tab as follows:

        If the tab is the active tab for the tab group, in which
        the class ``"active"`` will be added.

        If the tab is not enabled, the classes the class ``"disabled"``
        will be added.
        """
        default_classes = super(Tab, self).get_default_classes()
        if self.is_active():
            default_classes.extend(CSS_ACTIVE_TAB_CLASSES)
        if not self._enabled:
            default_classes.extend(CSS_DISABLED_TAB_CLASSES)
        return default_classes

    def get_template_name(self, request):
        """
        Returns the name of the template to be used for rendering this tab.

        By default it returns the value of the ``template_name`` attribute
        on the ``Tab`` class.
        """
        if not hasattr(self, "template_name"):
            raise AttributeError("%s must have a template_name attribute or "
                                 "override the get_template_name method."
                                 % self.__class__.__name__)
        return self.template_name

    def get_context_data(self, request):
        """
        This method should return a dictionary of context data used to render
        the tab. Required.
        """
        raise NotImplementedError("%s needs to define a get_context_data "
                                  "method." % self.__class__.__name__)

    def enabled(self, request):
        """
        Determines whether or not the tab should be accessible
        (e.g. be rendered into the HTML on load and respond to a click event).

        If a tab returns ``False`` from ``enabled`` it will ignore the value
        of ``preload`` and only render the HTML of the tab after being clicked.

        The default behavior is to return ``True`` for all cases.
        """
        return True

    def allowed(self, request):
        """
        Determines whether or not the tab is displayed.

        Tab instances can override this method to specify conditions under
        which this tab should not be shown at all by returning ``False``.

        The default behavior is to return ``True`` for all cases.
        """
        return True
