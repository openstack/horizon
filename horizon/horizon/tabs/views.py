from django import http
from django.views import generic

from horizon import exceptions


class TabView(generic.TemplateView):
    """
    A generic class-based view for displaying a :class:`horizon.tabs.TabGroup`.

    This view handles selecting specific tabs and deals with AJAX requests
    gracefully.

    .. attribute:: tab_group_class

        The only required attribute for ``TabView``. It should be a class which
        inherits from :class:`horizon.tabs.TabGroup`.
    """
    tab_group_class = None

    def __init__(self):
        if not self.tab_group_class:
            raise AttributeError("You must set the tab_group attribute on %s."
                                 % self.__class__.__name__)

    def get_tabs(self, request, *args, **kwargs):
        return self.tab_group_class(request, **kwargs)

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        try:
            tab_group = self.get_tabs(request, *args, **kwargs)
            context["tab_group"] = tab_group
        except:
            exceptions.handle(request)

        if request.is_ajax():
            if tab_group.selected:
                return http.HttpResponse(tab_group.selected.render())
            else:
                return http.HttpResponse(tab_group.render())
        return self.render_to_response(context)
