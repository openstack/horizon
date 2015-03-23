===================
Customizing Horizon
===================

Themes
======

As of the Kilo release, styling for the OpenStack Dashboard can be altered
through the use of a theme. A theme is a directory containing a
``_variables.scss`` file to override the color codes used throughout the SCSS
and a ``_styles.scss`` file with additional styles to load after dashboard
styles have loaded.

To use a custom theme, set ``CUSTOM_THEME_PATH`` in ``local_settings.py`` to
the directory location for the theme (e.g., ``"static/themes/blue"``). The
path can either be relative to the ``openstack_dashboard`` directory or an
absolute path to an accessible location on the file system. The default
``CUSTOM_THEME_PATH`` is ``static/themes/default``.

Both the Dashboard custom variables and Bootstrap variables can be overridden.
For a full list of the Dashboard SCSS variables that can be changed, see the
variables file at ``openstack_dashboard/static/dashboard/scss/_variables.scss``.

Changing the Logo
-----------------

There are currently two places where the OpenStack logo is pulled in
through the stylesheets. The first is shown at the login screen and the other
on top of the menu bar. To override the logo place your logo in your themes
directory and set the image to use in ``_styles.scss``. For example::

    #splash .login {
      background-image: url(/static/themes/THEME/logo-splash.png);
    }

    .topbar {
      h1.brand a {
        background-image: url(/static/themes/THEME/logo.png);
      }
    }

``THEME`` should be replaced by the name of your theme directory.
The dimensions should be ``width: 216px, height: 35px`` for a drop in
replacement.

Prior to the Kilo release the images files inside of Horizon needed to be
replaced by your images files or the Horizon stylesheets needed to be altered
to point to the location of your image.

Changing the Site Title
=======================

The OpenStack Dashboard Site Title branding (i.e. "**OpenStack** Dashboard")
can be overwritten by adding the attribute ``SITE_BRANDING``
to ``local_settings.py`` with the value being the desired name.

The file ``local_settings.py`` can be found at the Horizon directory path of
``openstack_dashboard/local/local_settings.py``.

Changing the Brand Link
=======================

The logo also acts as a hyperlink. The default behavior is to redirect to
``horizon:user_home``. By adding the attribute ``SITE_BRANDING_LINK`` with
the desired url target e.g., ``http://sample-company.com`` in
``local_settings.py``, the target of the hyperlink can be changed.

Modifying Existing Dashboards and Panels
========================================

If you wish to alter dashboards or panels which are not part of your codebase,
you can specify a custom python module which will be loaded after the entire
Horizon site has been initialized, but prior to the URLconf construction.
This allows for common site-customization requirements such as:

* Registering or unregistering panels from an existing dashboard.
* Changing the names of dashboards and panels.
* Re-ordering panels within a dashboard or panel group.

To specify the python module containing your modifications, add the key
``customization_module`` to your ``HORIZON_CONFIG`` dictionary in
``local_settings.py``. The value should be a string containing the path to your
module in dotted python path notation. Example::

    HORIZON_CONFIG = {
        "customization_module": "my_project.overrides"
    }

You can do essentially anything you like in the customization module. For
example, you could change the name of a panel::

    from django.utils.translation import ugettext_lazy as _

    import horizon

    # Rename "User Settings" to "User Options"
    settings = horizon.get_dashboard("settings")
    user_panel = settings.get_panel("user")
    user_panel.name = _("User Options")

Or get the instances panel::

    projects_dashboard = horizon.get_dashboard("project")
    instances_panel = projects_dashboard.get_panel("instances")

And limit access to users with the Keystone Admin role::

    permissions = list(getattr(instances_panel, 'permissions', []))
    permissions.append('openstack.roles.admin')
    instances_panel.permissions = tuple(permissions)

Or just remove it entirely::

    projects_dashboard.unregister(instances_panel.__class__)

You can also override existing methods with your own versions::

    # Disable Floating IPs
    from openstack_dashboard.dashboards.project.access_and_security import tabs
    from openstack_dashboard.dashboards.project.instances import tables

    NO = lambda *x: False

    tabs.FloatingIPsTab.allowed = NO
    tables.AssociateIP.allowed = NO
    tables.SimpleAssociateIP.allowed = NO
    tables.SimpleDisassociateIP.allowed = NO

You could also customize what columns are displayed in an existing
table, by redefining the ``columns`` attribute of its ``Meta``
class. This can be achieved in 3 steps:

#. Extend the table that you wish to modify
#. Redefine the ``columns`` attribute under the ``Meta`` class for this
   new table
#. Modify the ``table_class`` attribute for the related view so that it
   points to the new table


For example, if you wished to remove the Admin State column from the
:class:`~openstack_dashboard.dashboards.admin.networks.tables.NetworksTable`,
you could do the following::

    from openstack_dashboard.dashboards.project.networks import tables
    from openstack_dashboard.dashboards.project.networks import views

    class MyNetworksTable(tables.NetworksTable):

        class Meta(tables.NetworksTable.Meta):
            columns = ('name', 'subnets', 'shared', 'status')

    views.IndexView.table_class = MyNetworksTable

If you want to add a column you can override the parent table in a
similar way, add the new column definition and then use the ``Meta``
``columns`` attribute to control the column order as needed.

.. NOTE::

    ``my_project.overrides`` needs to be importable by the python process running
    Horizon.
    If your module is not installed as a system-wide python package,
    you can either make it installable (e.g., with a setup.py)
    or you can adjust the python path used by your WSGI server to include its location.

    Probably the easiest way is to add a ``python-path`` argument to
    the ``WSGIDaemonProcess`` line in Apache's Horizon config.

    Assuming your ``my_project`` module lives in ``/opt/python/my_project``,
    you'd make it look like the following::

        WSGIDaemonProcess [... existing options ...] python-path=/opt/python


Button Icons
============

Horizon uses font icons (glyphicons) from Twitter Bootstrap to add icons to buttons.
Please see http://bootstrapdocs.com/v3.1.1/docs/components/#glyphicons for instructions
how to use icons in the code.

To add icon to Table Action, use icon property. Example:

    class CreateSnapshot(tables.LinkAction):
       name = "snapshot"
       verbose_name = _("Create Snapshot")
       icon = "camera"

Additionally, the site-wide default button classes can be configured by
setting ``ACTION_CSS_CLASSES`` to a tuple of the classes you wish to appear
on all action buttons in your ``local_settings.py`` file.


Custom Stylesheets
==================

It is possible to define custom stylesheets for your dashboards. Horizon's base
template ``horizon/templates/base.html`` defines multiple blocks that
can be overridden.

To define custom css files that apply only to a specific dashboard, create
a base template in your dashboard's templates folder, which extends Horizon's
base template e.g. ``openstack_dashboard/dashboards/my_custom_dashboard/
templates/my_custom_dashboard/base.html``.

In this template, redefine ``block css``. (Don't forget to include
``_stylesheets.html`` which includes all Horizon's default stylesheets.)::

    {% extends 'base.html' %}

    {% block css %}
      {% include "_stylesheets.html" %}

      {% load compress %}
      {% compress css %}
      <link href='{{ STATIC_URL }}my_custom_dashboard/scss/my_custom_dashboard.scss' type='text/scss' media='screen' rel='stylesheet' />
      {% endcompress %}
    {% endblock %}

The custom stylesheets then reside in the dashboard's own ``static`` folder
``openstack_dashboard/dashboards/my_custom_dashboard/static/
my_custom_dashboard/scss/my_custom_dashboard.scss``.

All dashboard's templates have to inherit from dashboard's base.html::

    {% extends 'my_custom_dashboard/base.html' %}
    ...


Custom Javascript
=================

Similarly to adding custom styling (see above), it is possible to include
custom javascript files.

All Horizon's javascript files are listed in the ``horizon/_scripts.html``
partial template, which is included in Horizon's base template in ``block js``.

To add custom javascript files, create an ``_scripts.html`` partial template in
your dashboard ``openstack_dashboard/dashboards/my_custom_dashboard/
templates/my_custom_dashboard/_scripts.html`` which extends
``horizon/_scripts.html``. In this template override the
``block custom_js_files`` including your custom javascript files::

    {% extends 'horizon/_scripts.html' %}

    {% block custom_js_files %}
        <script src='{{ STATIC_URL }}my_custom_dashboard/js/my_custom_js.js' type='text/javascript' charset='utf-8'></script>
    {% endblock %}


In your dashboard's own base template ``openstack_dashboard/dashboards/
my_custom_dashboard/templates/my_custom_dashboard/base.html`` override
``block js`` with inclusion of dashboard's own ``_scripts.html``::

    {% block js %}
        {% include "my_custom_dashboard/_scripts.html" %}
    {% endblock %}

The result is a single compressed js file consisting both Horizon and
dashboard's custom scripts.

Additionally, some marketing and analytics scripts require you to place them
within the page's <head> tag. To do this, place them within the
``horizon/_custom_head_js.html`` file. Similar to the ``_scripts.html`` file
mentioned above, you may link to an existing file::

    <script src='{{ STATIC_URL }}/my_custom_dashboard/js/my_marketing_js.js' type='text/javascript' charset='utf-8'></script>

or you can paste your script directly in the file, being sure to use
appropriate tags::

  <script type="text/javascript">
  //some javascript
  </script>


Customizing Meta Attributes
===========================

To add custom metadata attributes to your project's base template, include
them in the ``horizon/_custom_meta.html`` file. The contents of this file will be
inserted into the page's <head> just after the default Horizon meta tags.
