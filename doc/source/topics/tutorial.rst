===================
Building on Horizon
===================

This tutorial covers how to use the various components in Horizon to build
an example dashboard and panel with a data table and tabs.

As an example, we'll build on the Nova instances API to create a new and novel
"visualizations" dashboard with a "flocking" panel that presents the instance
data in a different manner.

You can find a reference implementation of the code being described here
on github at https://github.com/gabrielhurley/horizon_demo.

.. note::

    There are a variety of other resources which may be helpful to read first,
    since this is a more advanced tutorial. For example, you may want to start
    with the :doc:`Horizon quickstart guide </quickstart>` or the
    `Django tutorial`_.

    .. _Django tutorial: https://docs.djangoproject.com/en/1.4/intro/tutorial01/


Creating a dashboard
====================

.. note::

    It is perfectly valid to create a panel without a dashboard, and
    incorporate it into an existing dashboard. See the section
    :ref:`overrides <overrides>` later in this document.

The quick version
-----------------

Horizon provides a custom management command to create a typical base
dashboard structure for you. The following command generates most of the
boilerplate code explained below::

    ./run_tests.sh -m startdash visualizations

It's still recommended that you read the rest of this section to understand
what that command creates and why.

Structure
---------

The recommended structure for a dashboard (or panel) follows suit with the
typical Django application layout. We'll name our dashboard "visualizations"::

    visualizations
      |--__init__.py
      |--dashboard.py
      |--templates/
      |--static/

The ``dashboard.py`` module will contain our dashboard class for use by
Horizon; the ``templates`` and ``static`` directories give us homes for our
Django template files and static media respectively.

Within the ``static`` and ``templates`` directories it's generally good to
namespace your files like so::

    templates/
      |--visualizations/
    static/
      |--visualizations/
         |--css/
         |--js/
         |--img/

With those files and directories in place, we can move on to writing our
dashboard class.


Defining a dashboard
--------------------

A dashboard class can be incredibly simple (about 3 lines at minimum),
defining nothing more than a name and a slug::

    import horizon

    class VizDash(horizon.Dashboard):
        name = _("Visualizations")
        slug = "visualizations"

In practice, a dashboard class will usually contain more information, such as a
list of panels, which panel is the default, and any permissions required to
access this dashboard::

    class VizDash(horizon.Dashboard):
        name = _("Visualizations")
        slug = "visualizations"
        panels = ('flocking',)
        default_panel = 'flocking'
        permissions = ('openstack.roles.admin',)

Building from that previous example we may also want to define a grouping of
panels which share a common theme and have a sub-heading in the navigation::

    class InstanceVisualizations(horizon.PanelGroup):
        slug = "instance_visualizations"
        name = _("Instance Visualizations")
        panels = ('flocking',)


    class VizDash(horizon.Dashboard):
        name = _("Visualizations")
        slug = "visualizations"
        panels = (InstanceVisualizations,)
        default_panel = 'flocking'
        permissions = ('openstack.roles.admin',)

The ``PanelGroup`` can be added to the dashboard class' ``panels`` list
just like the slug of the panel can.

Once our dashboard class is complete, all we need to do is register it::

    horizon.register(VizDash)

The typical place for that would be the bottom of the ``dashboard.py`` file,
but it could also go elsewhere, such as in an override file (see below).


Creating a panel
================

Now that we have our dashboard written, we can also create our panel. We'll
call it "flocking".

.. note::

    You don't need to write a custom dashboard to add a panel. The structure
    here is for the sake of completeness in the tutorial.

The quick version
-----------------

Horizon provides a custom management command to create a typical base
panel structure for you. The following command generates most of the
boilerplate code explained below::

    ./run_tests.sh -m startpanel flocking --dashboard=visualizations --target=auto

The ``dashboard`` argument is required, and tells the command which dashboard
this panel will be registered with. The ``target`` argument is optional, and
respects ``auto`` as a special value which means that the files for the panel
should be created inside the dashboard module as opposed to the current
directory (the default).

It's still recommended that you read the rest of this section to understand
what that command creates and why.

Structure
---------

A panel is a relatively flat structure with the exception that templates
for a panel in a dashboard live in the dashboard's ``templates`` directory
rather than in the panel's ``templates`` directory. Continuing our
vizulaization/flocking example, let's see what the looks like::

    # stand-alone panel structure
    flocking/
      |--__init__.py
      |--panel.py
      |--urls.py
      |--views.py
      |--templates/
         |--flocking/
            |--index.html

    # panel-in-a-dashboard structure
    visualizations/
    |--__init__.py
    |--dashboard.py
    |--flocking/
       |--__init__.py
       |--panel.py
       |--urls.py
       |--views.py
    |--templates/
       |--visualizations/
          |--flocking/
             |--index.html

That follows standard Django namespacing conventions for apps and submodules
within apps. It also works cleanly with Django's automatic template discovery
in both cases.

Defining a panel
----------------

The ``panel.py`` file referenced above has a special meaning. Within a
dashboard, any module name listed in the ``panels`` attribute on the
dashboard class will be auto-discovered by looking for ``panel.py`` file
in a corresponding directory (the details are a bit magical, but have been
thoroughly vetted in Django's admin codebase).

Inside the ``panel.py`` module we define our ``Panel`` class::

    class Flocking(horizon.Panel):
        name = _("Flocking")
        slug = 'flocking'

Simple, right? Once we've defined it, we register it with the dashboard::

    from visualizations import dashboard

    dashboard.VizDash.register(Flocking)

Easy! There are more options you can set to customize the ``Panel`` class, but
it makes some intelligent guesses about what the defaults should be.

URLs
----

One of the intelligent assumptions the ``Panel`` class makes is that it can
find a ``urls.py`` file in your panel directory which will define a view named
``index`` that handles the default view for that panel. This is what your
``urls.py`` file might look like::

    from django.conf.urls.defaults import patterns, url
    from .views import IndexView

    urlpatterns = patterns('',
        url(r'^$', IndexView.as_view(), name='index')
    )

There's nothing there that isn't 100% standard Django code. This example
(and Horizon in general) uses the class-based views introduced in Django 1.3
to make code more reusable. Hence the view class is imported in the example
above, and the ``as_view()`` method is called in the URL pattern.

This, of course, presumes you have a view class, and takes us into the meat
of writing a ``Panel``.


Tables, Tabs, and Views
-----------------------

Now we get to the really exciting parts; everything before this was structural.

Starting with the high-level view, our end goal is to create a view (our
``IndexView`` class referenced above) which uses Horizon's ``DataTable``
class to display data and Horizon's ``TabGroup`` class to give us a
user-friendly tabbed interface in the browser.

We'll start with the table, combine that with the tabs, and then build our
view from the pieces.

Defining a table
~~~~~~~~~~~~~~~~

Horizon provides a :class:`~horizon.tables.DataTable` class which simplifies
the vast majority of displaying data to an end-user. We're just going to skim
the surface here, but it has a tremendous number of capabilities.

In this case, we're going to be presenting data about tables, so let's start
defining our table (and a ``tables.py`` module::

    from horizon import tables

    class FlockingInstancesTable(tables.DataTable):
        host = tables.Column("OS-EXT-SRV-ATTR:host", verbose_name=_("Host"))
        tenant = tables.Column('tenant_name', verbose_name=_("Tenant"))
        user = tables.Column('user_name', verbose_name=_("user"))
        vcpus = tables.Column('flavor_vcpus', verbose_name=_("VCPUs"))
        memory = tables.Column('flavor_memory', verbose_name=_("Memory"))
        age = tables.Column('age', verbose_name=_("Age"))

        class Meta:
            name = "instances"
            verbose_name = _("Instances")

There are several things going on here... we created a table subclass,
and defined six columns on it. Each of those columns defines what attribute
it accesses on the instance object as the first argument, and since we like to
make everything translatable, we give each column a ``verbose_name`` that's
marked for translation.

Lastly, we added a ``Meta`` class which defines some properties about our
table, notably it's (translatable) verbose name, and a semi-unique "slug"-like
name to identify it.

.. note::

    This is a slight simplification from the reality of how the instance
    object is actually structured. In reality, accessing the flavor, tenant,
    and user attributes on it requires an additional step. This code can be
    seen in the example code available on github.

Defining tabs
~~~~~~~~~~~~~

So we have a table, ready to receive our data. We could go straight to a view
from here, but we can think bigger. In this case we're also going to use
Horizon's :class:`~horizon.tabs.TabGroup` class. This gives us a clean,
no-fuss tabbed interface to display both our visualization and, optionally,
our data table.

First off, let's make a tab for our visualization::

    class VizTab(tabs.Tab):
        name = _("Visualization")
        slug = "viz"
        template_name = "visualizations/flocking/_flocking.html"

        def get_context_data(self, request):
            return None

This is about as simple as you can get. Since our visualization will
ultiimately use AJAX to load it's data we don't need to pass any context
to the template, and all we need to define is the name and which template
it should use.

Now, we also need a tab for our data table::

    from .tables import FlockingInstancesTable

    class DataTab(tabs.TableTab):
        name = _("Data")
        slug = "data"
        table_classes = (FlockingInstancesTable,)
        template_name = "horizon/common/_detail_table.html"
        preload = False

        def get_instances_data(self):
            try:
                instances = utils.get_instances_data(self.tab_group.request)
            except:
                instances = []
                exceptions.handle(self.tab_group.request,
                                  _('Unable to retrieve instance list.'))
            return instances

This tab gets a little more complicated. Foremost, it's a special type of
tab--one that handles data tables (and all their associated features)--and
it also uses the ``preload`` attribute to specify that this tab shouldn't
be loaded by default. It will instead be loaded via AJAX when someone clicks
on it, saving us on API calls in the vast majority of cases.

Lastly, this code introduces the concept of error handling in Horizon.
The :func:`horizon.exceptions.handle` function is a centralized error
handling mechanism that takes all the guess-work and inconsistency out of
dealing with exceptions from the API. Use it everywhere.

Tying it together in a view
~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are lots of pre-built class-based views in Horizon. We try to provide
starting points for all the common combinations of components.

In this case we want a starting view type that works with both tabs and
tables... that'd be the :class:`~horizon.tabs.TabbedTableView` class. It takes
the best of the dynamic delayed-loading capabilities tab groups provide and
mixes in the actions and AJAX-updating that tables are capable of with almost
no work on the user's end. Let's see what the code would look like::

    from .tables import FlockingInstancesTable
    from .tabs import FlockingTabs

    class IndexView(tabs.TabbedTableView):
        tab_group_class = FlockingTabs
        table_class = FlockingInstancesTable
        template_name = 'visualizations/flocking/index.html'

That would get us 100% of the way to what we need if this particular
demo didn't involve an extra AJAX call to fetch back our visualization
data via AJAX. Because of that we need to override the class' ``get()``
method to return the right data for an AJAX call::

    from .tables import FlockingInstancesTable
    from .tabs import FlockingTabs

    class IndexView(tabs.TabbedTableView):
        tab_group_class = FlockingTabs
        table_class = FlockingInstancesTable
        template_name = 'visualizations/flocking/index.html'

        def get(self, request, *args, **kwargs):
            if self.request.is_ajax() and self.request.GET.get("json", False):
                try:
                    instances = utils.get_instances_data(self.request)
                except:
                    instances = []
                    exceptions.handle(request,
                                      _('Unable to retrieve instance list.'))
                data = json.dumps([i._apiresource._info for i in instances])
                return http.HttpResponse(data)
            else:
                return super(IndexView, self).get(request, *args, **kwargs)

In this instance, we override the ``get()`` method such that if it's an
AJAX request and has the GET parameter we're looking for, it returns our
instance data in JSON format; otherwise it simply returns the view function
as per the usual.

The template
~~~~~~~~~~~~

We need three templates here: one for the view, and one for each of our two
tabs. The view template (in this case) can inherit from one of the other
dashboards::

    {% extends 'base.html' %}
    {% load i18n %}
    {% block title %}{% trans "Flocking" %}{% endblock %}

    {% block page_header %}
      {% include "horizon/common/_page_header.html" with title=_("Flocking") %}
    {% endblock page_header %}

    {% block main %}
    <div class="row-fluid">
      <div class="span12">
      {{ tab_group.render }}
      </div>
    </div>
    {% endblock %}

This gives us a custom page title, a header, and render our tab group provided
by the view.

For the tabs, the one using the table is handled by a reusable template,
``"horizon/common/_detail_table.html"``. This is appropriate for any tab that
only displays a single table.

The second tab is a bit of secret sauce for the visualization, but it's still
quite simple and can be investigated in the github example.

The takeaway here is that each tab needs a template associated with it.

With all our code in place, the only thing left to do is to integrated it into
our OpenStack Dashboard site.

Setting up a project
====================

The vast majority of people will just customize the OpenStack Dashboard
example project that ships with Horizon. As such, this tutorial will
start from that and just illustrate the bits that can be customized.

Structure
---------

A site built on Horizon takes the form of a very typical Django project::

    site/
      |--__init__.py
      |--manage.py
      |--demo_dashboard/
         |--__init__.py
         |--models.py  # required for Django even if unused
         |--settings.py
         |--templates/
         |--static/

The key bits here are that ``demo_dashboard`` is on our python path, and that
the `settings.py`` file here will contain our customized Horizon config.

The settings file
-----------------

There are several key things you will generally want to customiz in your
site's settings file: specifying custom dashboards and panels, catching your
client's exception classes, and (possibly) specifying a file for advanced
overrides.

Specifying dashboards
~~~~~~~~~~~~~~~~~~~~~

The most basic thing to do is to add your own custom dashboard using the
``HORIZON_CONFIG`` dictionary in the settings file::

    HORIZON_CONFIG = {
        'dashboards': ('project', 'admin', 'settings',),
    }

Please note, the dashboards also must be added to settings.py::
    INSTALLED_APPS = (
        'openstack_dashboard',
        ...
        'horizon',
        'openstack_dashboard.dashboards.project',
        'openstack_dashboard.dashboards.admin',
        'openstack_dashboard.dashboards.settings',
        ...
    )

In this case, we've taken the default Horizon ``'dashboards'`` config and
added our ``visualizations`` dashboard to it. Note that the name here is the
name of the dashboard's module on the python path. It will find our
``dashboard.py`` file inside of it and load both the dashboard and its panels
automatically from there.

Error handling
~~~~~~~~~~~~~~

Adding custom error handler for your API client is quite easy. While it's not
necessary for this example, it would be done by customizing the
``'exceptions'`` value in the ``HORIZON_CONFIG`` dictionary::

    import my_api.exceptions as my_api

    'exceptions': {'recoverable': [my_api.Error,
                                   my_api.ClientConnectionError],
                   'not_found': [my_api.NotFound],
                   'unauthorized': [my_api.NotAuthorized]},

.. _overrides:

Override file
~~~~~~~~~~~~~

The override file is the "god-mode" dashboard editor. The hook for this file
sits right between the automatic discovery mechanisms and the final setup
routines for the entire site. By specifying an override file you can alter
any behavior you like in existing code. This tutorial won't go in-depth,
but let's just say that with great power comes great responsibility.

To specify am override file, you set the ``'customization_module'`` value in
the ``HORIZON_CONFIG`` dictionary to the dotted python path of your
override module::

    HORIZON_CONFIG = {
        'customization_module': 'demo_dashboard.overrides'
    }

This file is capable of adding dashboards, adding panels to existing
dashboards, renaming existing dashboards and panels (or altering other
attributes on them), removing panels from existing dashboards, and so on.

We could say more, but it only gets more dangerous...

Conclusion
==========

Sadly, the cake was a lie. The information in this "tutorial" was never
meant to leave you with a working dashboard. It's close. But there's
waaaaaay too much javascript involved in the visualization to cover it all
here, and it'd be irrelevant to Horizon anyway.

If you want to see the finished product, check out the github example
referenced at the beginning of this tutorial.

Clone the repository and simply run ``./run_tests.sh --runserver``. That'll
give you a 100% working dashboard that uses every technique in this tutorial.

What you've learned here, however, is the fundamentals of almost everything
you need to know to start writing interfaces for your own project based on the
components Horizon provides.

If you have questions, or feedback on how this tutorial could be improved,
please feel free to pass them along!
