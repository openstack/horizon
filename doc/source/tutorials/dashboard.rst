============================================
Tutorial: Building a Dashboard using Horizon
============================================

This tutorial covers how to use the various components in horizon to build
an example dashboard and a panel with a tab which has a table containing data
from the back end.

As an example, we'll create a new ``My Dashboard`` dashboard with a ``My Panel``
panel that has an ``Instances Tab`` tab. The tab has a table which contains the
data pulled by the Nova instances API.


.. note::

    This tutorial assumes you have either a ``devstack`` or ``openstack``
    environment up and running.
    There are a variety of other resources which may be helpful to read first.
    For example, you may want to start
    with the :doc:`Horizon quickstart guide </quickstart>` or the
    `Django tutorial`_.

    .. _Django tutorial: https://docs.djangoproject.com/en/1.6/intro/tutorial01/


Creating a dashboard
====================

The quick version
-----------------

Horizon provides a custom management command to create a typical base
dashboard structure for you. Run the following commands at the same location
where the ``run_tests.sh`` file resides. It generates most of the boilerplate
code you need::

    mkdir openstack_dashboard/dashboards/mydashboard

    ./run_tests.sh -m startdash mydashboard \
                  --target openstack_dashboard/dashboards/mydashboard

    mkdir openstack_dashboard/dashboards/mydashboard/mypanel

    ./run_tests.sh -m startpanel mypanel \
                   --dashboard=openstack_dashboard.dashboards.mydashboard \
                   --target=openstack_dashboard/dashboards/mydashboard/mypanel


You will notice that the directory ``mydashboard`` gets automatically
populated with the files related to a dashboard and the ``mypanel`` directory
gets automatically populated with the files related to a panel.


Structure
---------
If you use the ``tree mydashboard`` command to list the ``mydashboard``
directory in ``openstack_dashboard/dashboards`` , you will see a directory
structure that looks like the following::

    mydashboard
    ├── dashboard.py
    ├── dashboard.pyc
    ├── __init__.py
    ├── __init__.pyc
    ├── mypanel
    │   ├── __init__.py
    │   ├── panel.py
    │   ├── templates
    │   │   └── mypanel
    │   │       └── index.html
    │   ├── tests.py
    │   ├── urls.py
    │   └── views.py
    ├── static
    │   └── mydashboard
    │       ├── css
    │       │   └── mydashboard.css
    │       └── js
    │           └── mydashboard.js
    └── templates
        └── mydashboard
            └── base.html


For this tutorial, we will not deal with the static directory, or the
``tests.py`` file. Leave them as they are.

With the rest of the files and directories in place, we can move on to add our
own dashboard.


Defining a dashboard
--------------------

Open the ``dashboard.py`` file. You will notice the following code has been
automatically generated::

   from django.utils.translation import ugettext_lazy as _

   import horizon


   class Mydashboard(horizon.Dashboard):
      name = _("Mydashboard")
      slug = "mydashboard"
      panels = ()           # Add your panels here.
      default_panel = ''    # Specify the slug of the dashboard's default panel.


   horizon.register(Mydashboard)


If you want the dashboard name to be something else, you can change the ``name``
attribute in the ``dashboard.py`` file . For example, you can change it
to be ``My Dashboard`` ::

    name = _("My Dashboard")


A dashboard class will usually contain a ``name`` attribute (the display name of
the dashboard), a ``slug`` attribute (the internal name that could be referenced
by other components), a list of panels, default panel, etc. We will cover how
to add a panel in the next section.


Creating a panel
================

We'll create a panel and call it ``My Panel``.

Structure
---------

As described above, the ``mypanel`` directory under
``openstack_dashboard/dashboards/mydashboard`` should look like the following::

   mypanel
    ├── __init__.py
    ├── models.py
    ├── panel.py
    ├── templates
    │   └── mypanel
    │     └── index.html
    ├── tests.py
    ├── urls.py
    └── views.py


Defining a panel
----------------

The ``panel.py`` file referenced above has a special meaning. Within a dashboard,
any module name listed in the ``panels`` attribute on the dashboard class will
be auto-discovered by looking for the ``panel.py`` file in a corresponding
directory (the details are a bit magical, but have been thoroughly vetted in
Django's admin codebase).

Open the ``panel.py`` file, you will have the following auto-generated code::

    from django.utils.translation import ugettext_lazy as _

    import horizon

    from openstack_dashboard.dashboards.mydashboard import dashboard


    class Mypanel(horizon.Panel):
        name = _("Mypanel")
        slug = "mypanel"


    dashboard.Mydashboard.register(Mypanel)


If you want the panel name to be something else, you can change the ``name``
attribute in the ``panel.py`` file . For example, you can change it to be
``My Panel``::

    name = _("My Panel")


Open the ``dashboard.py`` file again, insert the following code above the
``Mydashboard`` class. This code defines the ``Mygroup`` class and adds a panel
called ``mypanel``::

    class Mygroup(horizon.PanelGroup):
        slug = "mygroup"
        name = _("My Group")
        panels = ('mypanel',)


Modify the ``Mydashboard`` class to include ``Mygroup`` and add ``mypanel`` as
the default panel::

     class Mydashboard(horizon.Dashboard):
        name = _("My Dashboard")
        slug = "mydashboard"
        panels = (Mygroup,)  # Add your panels here.
        default_panel = 'mypanel'  # Specify the slug of the default panel.


The completed ``dashboard.py`` file should look like
the following::

    from django.utils.translation import ugettext_lazy as _

    import horizon


    class Mygroup(horizon.PanelGroup):
        slug = "mygroup"
        name = _("My Group")
        panels = ('mypanel',)


    class Mydashboard(horizon.Dashboard):
        name = _("My Dashboard")
        slug = "mydashboard"
        panels = (Mygroup,)  # Add your panels here.
        default_panel = 'mypanel'  # Specify the slug of the default panel.


    horizon.register(Mydashboard)



Tables, Tabs, and Views
-----------------------

We'll start with the table, combine that with the tabs, and then build our
view from the pieces.

Defining a table
~~~~~~~~~~~~~~~~

Horizon provides a :class:`~horizon.forms.SelfHandlingForm`  :class:`~horizon.tables.DataTable` class which simplifies
the vast majority of displaying data to an end-user. We're just going to skim
the surface here, but it has a tremendous number of capabilities.

Create a ``tables.py`` file under the ``mypanel`` directory and add the
following code::

    from django.utils.translation import ugettext_lazy as _

    from horizon import tables


    class InstancesTable(tables.DataTable):
        name = tables.Column("name", verbose_name=_("Name"))
        status = tables.Column("status", verbose_name=_("Status"))
        zone = tables.Column('availability_zone',
                              verbose_name=_("Availability Zone"))
        image_name = tables.Column('image_name', verbose_name=_("Image Name"))

        class Meta:
            name = "instances"
            verbose_name = _("Instances")


There are several things going on here... we created a table subclass,
and defined four columns that we want to retrieve data and display.
Each of those columns defines what attribute it accesses on the instance object
as the first argument, and since we like to make everything translatable,
we give each column a ``verbose_name`` that's marked for translation.

Lastly, we added a ``Meta`` class which indicates the meta object that describes
the ``instances`` table.

.. note::

    This is a slight simplification from the reality of how the instance
    object is actually structured. In reality, accessing other attributes
    requires an additional step.

Adding actions to a table
~~~~~~~~~~~~~~~~~~~~~~~~~

Horizon provides three types of basic action classes which can be taken
on a table's data:

- :class:`~horizon.tables.Action`
- :class:`~horizon.tables.LinkAction`
- :class:`~horizon.tables.FilterAction`


There are also additional actions which are extensions of the basic Action classes:

- :class:`~horizon.tables.BatchAction`
- :class:`~horizon.tables.DeleteAction`
- :class:`~horizon.tables.UpdateAction`
- :class:`~horizon.tables.FixedFilterAction`



Now let's create and add a filter action to the table. To do so, we will need
to edit the ``tables.py`` file used above. To add a filter action which will
only show rows which contain the string entered in the filter field, we
must first define the action::

    class MyFilterAction(tables.FilterAction):
        name = "myfilter"


.. note::

    The action specified above will default the ``filter_type`` to be ``"query"``.
    This means that the filter will use the client side table sorter.

Then, we add that action to the table actions for our table.::

    class InstancesTable:
        class Meta:
            table_actions = (MyFilterAction,)


The completed ``tables.py`` file should look like the following::

    from django.utils.translation import ugettext_lazy as _

    from horizon import tables


    class MyFilterAction(tables.FilterAction):
        name = "myfilter"


    class InstancesTable(tables.DataTable):
        name = tables.Column('name', \
                             verbose_name=_("Name"))
        status = tables.Column('status', \
                               verbose_name=_("Status"))
        zone = tables.Column('availability_zone', \
                             verbose_name=_("Availability Zone"))
        image_name = tables.Column('image_name', \
                                   verbose_name=_("Image Name"))

        class Meta:
            name = "instances"
            verbose_name = _("Instances")
            table_actions = (MyFilterAction,)


Defining tabs
~~~~~~~~~~~~~

So we have a table, ready to receive our data. We could go straight to a view
from here, but in this case we're also going to use horizon's
:class:`~horizon.tabs.TabGroup` class.

Create a ``tabs.py`` file under the ``mypanel`` directory. Let's make a tab
group which has one tab. The completed code should look like the following::


    from django.utils.translation import ugettext_lazy as _

    from horizon import exceptions
    from horizon import tabs

    from openstack_dashboard import api
    from openstack_dashboard.dashboards.mydashboard.mypanel import tables


    class InstanceTab(tabs.TableTab):
        name = _("Instances Tab")
        slug = "instances_tab"
        table_classes = (tables.InstancesTable,)
        template_name = ("horizon/common/_detail_table.html")
        preload = False

        def has_more_data(self, table):
            return self._has_more

        def get_instances_data(self):
            try:
                marker = self.request.GET.get(
                            tables.InstancesTable._meta.pagination_param, None)

                instances, self._has_more = api.nova.server_list(
                    self.request,
                    search_opts={'marker': marker, 'paginate': True})

                return instances
            except Exception:
                self._has_more = False
                error_message = _('Unable to get instances')
                exceptions.handle(self.request, error_message)

                return []

    class MypanelTabs(tabs.TabGroup):
        slug = "mypanel_tabs"
        tabs = (InstanceTab,)
        sticky = True


This tab gets a little more complicated. The tab handles data tables (and
all their associated features), and it also uses the ``preload`` attribute to
specify that this tab shouldn't be loaded by default. It will instead be loaded
via AJAX when someone clicks on it, saving us on API calls in the vast majority
of cases.

Additionally, the displaying of the table is handled by a reusable template,
``horizon/common/_detail_table.html``. Some simple pagination code was added
to handle large instance lists.

Lastly, this code introduces the concept of error handling in horizon.
The :func:`horizon.exceptions.handle` function is a centralized error
handling mechanism that takes all the guess-work and inconsistency out of
dealing with exceptions from the API. Use it everywhere.

Tying it together in a view
~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are lots of pre-built class-based views in horizon. We try to provide
the starting points for all the common combinations of components.

Open the ``views.py`` file, the auto-generated code is like the following::

    from horizon import views


    class IndexView(views.APIView):
        # A very simple class-based view...
        template_name = 'mydashboard/mypanel/index.html'

        def get_data(self, request, context, *args, **kwargs):
            # Add data to the context here...
            return context


In this case we want a starting view type that works with both tabs and
tables... that'd be the :class:`~horizon.tabs.TabbedTableView` class. It takes
the best of the dynamic delayed-loading capabilities tab groups provide and
mixes in the actions and AJAX-updating that tables are capable of with almost
no work on the user's end. Change ``views.APIView`` to be
``tabs.TabbedTableView`` and add ``MypanelTabs`` as the tab group class in the
``IndexView`` class::

    class IndexView(tabs.TabbedTableView):
        tab_group_class = mydashboard_tabs.MypanelTabs


After importing the proper package, the completed ``views.py`` file  now looks like
the following::

    from horizon import tabs

    from openstack_dashboard.dashboards.mydashboard.mypanel \
        import tabs as mydashboard_tabs


    class IndexView(tabs.TabbedTableView):
        tab_group_class = mydashboard_tabs.MypanelTabs
        template_name = 'mydashboard/mypanel/index.html'

        def get_data(self, request, context, *args, **kwargs):
            # Add data to the context here...
            return context


URLs
----
The auto-generated ``urls.py`` file is like::

    from django.conf.urls import url

    from openstack_dashboard.dashboards.mydashboard.mypanel import views


    urlpatterns = [
        url(r'^$', views.IndexView.as_view(), name='index'),
    ]


The template
~~~~~~~~~~~~

Open the ``index.html`` file in the ``mydashboard/mypanel/templates/mypanel``
directory, the auto-generated code is like the following::

    {% extends 'base.html' %}
    {% load i18n %}
    {% block title %}{% trans "Mypanel" %}{% endblock %}

    {% block page_header %}
        {% include "horizon/common/_page_header.html" with title=_("Mypanel") %}
    {% endblock page_header %}

    {% block main %}
    {% endblock %}


The ``main`` block must be modified to insert the following code::

   <div class="row">
      <div class="col-sm-12">
      {{ tab_group.render }}
      </div>
   </div>


If you want to change the title of the ``index.html`` file to be something else,
you can change it. For example, change it to be ``My Panel`` in the
``block title`` section.  If you want the ``title`` in the ``block page_header``
section to be something else, you can change it. For example, change it to be
``My Panel``. The updated code could be like::

   {% extends 'base.html' %}
   {% load i18n %}
   {% block title %}{% trans "My Panel" %}{% endblock %}

   {% block page_header %}
      {% include "horizon/common/_page_header.html" with title=_("My Panel") %}
   {% endblock page_header %}

   {% block main %}
   <div class="row">
      <div class="col-sm-12">
      {{ tab_group.render }}
      </div>
   </div>
   {% endblock %}


This gives us a custom page title, a header, and renders our tab group provided
by the view.

With all our code in place, the only thing left to do is to integrate it into
our OpenStack Dashboard site.


.. note::

    For more information about Django views, URLs and templates, please refer
    to the `Django documentation`_.

    .. _Django documentation: https://docs.djangoproject.com/en/1.6/


Enable and show the dashboard
=============================

In order to make ``My Dashboard`` show up along with the existing dashboards
like ``Project`` or ``Admin`` on horizon, you need to create a file called
``_50_mydashboard.py`` under ``openstack_dashboard/enabled`` and add the
following::

    # The name of the dashboard to be added to HORIZON['dashboards']. Required.
    DASHBOARD = 'mydashboard'

    # If set to True, this dashboard will not be added to the settings.
    DISABLED = False

    # A list of applications to be added to INSTALLED_APPS.
    ADD_INSTALLED_APPS = [
        'openstack_dashboard.dashboards.mydashboard',
    ]


Run and check the dashboard
===========================

Everything is in place, now run ``Horizon`` on the different port::

    ./run_tests.sh --runserver 0.0.0.0:8877


Go to ``http://<your server>:8877`` using a browser. After login as an admin
you should be able see ``My Dashboard`` shows up at the left side on horizon.
Click it, ``My Group`` will expand with ``My Panel``. Click on ``My Panel``,
the right side panel will display an ``Instances Tab`` which has an
``Instances`` table.

If you don't see any instance data, you haven't created any instances yet.  Go to
dashboard ``Project`` -> ``Images``, select a small image, for example,
``cirros-0.3.1-x86_64-uec`` , click ``Launch`` and enter an ``Instance Name``,
click the button ``Launch``. It should create an instance if the OpenStack or
devstack is correctly set up. Once the creation of an instance is successful, go
to ``My Dashboard`` again to check the data.


Adding a complex action to a table
==================================

For a more detailed look into adding a table action, one that requires forms for
gathering data, you can walk through :doc:`Adding a complex action to a table
</topics/table_actions>` tutorial.


Conclusion
==========

What you've learned here is the fundamentals of how to write interfaces for
your own project based on the components horizon provides.

If you have feedback on how this tutorial could be improved, please feel free
to submit a bug against ``Horizon`` in `launchpad`_.

    .. _launchpad: https://bugs.launchpad.net/horizon
