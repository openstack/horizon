.. _install-customizing:

===================
Customizing Horizon
===================

.. seealso::

   You may also be interested in :doc:`themes` and :doc:`branding`.

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

Customizing the Footer
======================

It is possible to customize the global and login footers by using Django's
recursive inheritance to extend the ``base.html``, ``auth/login.html``, and
``auth/_login_form.html`` templates. You do this by naming your template the
same name as the template you wish to extend and only overriding the blocks you
wish to change.

Your theme's ``base.html``::

    {% extends "base.html" %}

    {% block footer %}
      <p>My custom footer</p>
    {% endblock %}

Your theme's ``auth/login.html``::

    {% extends "auth/login.html" %}

    {% block footer %}
      <p>My custom login footer</p>
    {% endblock %}

Your theme's ``auth/_login_form.html``::

    {% extends "auth/_login_form.html" %}

    {% block login_footer %}
      {% comment %}
        You MUST have block.super because that includes the login button.
      {% endcomment %}
     {{ block.super }}
      <p>My custom login form footer</p>
    {% endblock %}

See the ``example`` theme for a working theme that uses these blocks.


Modifying Existing Dashboards and Panels
========================================

If you wish to alter dashboards or panels which are not part of your codebase,
you can specify a custom python module which will be loaded after the entire
Horizon site has been initialized, but prior to the URLconf construction.
This allows for common site-customization requirements such as:

* Registering or unregistering panels from an existing dashboard.
* Changing the names of dashboards and panels.
* Re-ordering panels within a dashboard or panel group.

Default Horizon panels are loaded based upon files within the
openstack_dashboard/enabled/ folder. These files are loaded based upon the
filename order, with space left for more files to be added. There are some
example files available within this folder, with the .example suffix
added. Developers and deployers should strive to use this method of
customization as much as possible, and support for this is given preference
over more exotic methods such as monkey patching and overrides files.

.. _horizon-customization-module:

Horizon customization module (overrides)
========================================

Horizon has a global overrides mechanism available to perform customizations
that are not yet customizable via configuration settings. This file can perform
monkey patching and other forms of customization which are not possible via the
enabled folder's customization method.

This method of customization is meant to be available for deployers of Horizon,
and use of this should be avoided by Horizon plugins at all cost. Plugins
needing this level of monkey patching and flexibility should instead look for
changing their __init__.py file and performing customizations through other
means.

To specify the python module containing your modifications, add the key
``customization_module`` to your ``HORIZON_CONFIG`` dictionary in
``local_settings.py``. The value should be a string containing the path to your
module in dotted python path notation. Example::

    HORIZON_CONFIG["customization_module"] = "my_project.overrides"

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

Or just remove it entirely::

    projects_dashboard.unregister(instances_panel.__class__)

You cannot unregister a ``default_panel``. If you wish to remove a
``default_panel``, you need to make a different panel in the dashboard as a
``default_panel`` and then unregister the former. For example, if you wished
to remove the ``overview_panel`` from the ``Project`` dashboard, you could do
the following::

    project = horizon.get_dashboard('project')
    project.default_panel = "instances"
    overview = project.get_panel('overview')
    project.unregister(overview.__class__)

You can also override existing methods with your own versions::

    from openstack_dashboard.dashboards.admin.info import tabs
    from openstack_dashboard.dashboards.project.instances import tables

    NO = lambda *x: False

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


Customize the project and user table columns
============================================


Keystone V3 has a place to store extra information regarding project and user.
Using the override mechanism described in :ref:`horizon-customization-module`,
Horizon is able to show these extra information as a custom column.
For example, if a user in Keystone has an attribute ``phone_num``, you could
define new column::

    from django.utils.translation import ugettext_lazy as _

    from horizon import forms
    from horizon import tables

    from openstack_dashboard.dashboards.identity.users import tables as user_tables
    from openstack_dashboard.dashboards.identity.users import views

    class MyUsersTable(user_tables.UsersTable):
        phone_num = tables.Column('phone_num',
                                  verbose_name=_('Phone Number'),
                                  form_field=forms.CharField(),)

        class Meta(user_tables.UsersTable.Meta):
            columns = ('name', 'description', 'phone_num')

    views.IndexView.table_class = MyUsersTable


Customize Angular dashboards
============================

In Angular, you may write a plugin to extend certain features. Two components
in the Horizon framework that make this possible are the extensibility service
and the resource type registry service. The ``extensibleService`` allows
certain Horizon elements to be extended dynamically, including add, remove, and
replace. The ``resourceTypeRegistry`` service provides methods to set and get
information pertaining to a resource type object. We use Heat type names like
``OS::Glance::Image`` as our reference name.

Some information you may place in the registry include:

* API to fetch data from
* Property names
* Actions (e.g. "Create Volume")
* URL paths to detail view or detail drawer
* Property information like labels or formatting for property values

These properties in the registry use the extensibility service (as of Newton
release):

* globalActions
* batchActions
* itemActions
* detailViews
* tableColumns
* filterFacets

Using the information from the registry, we can build out our dashboard panels.
Panels use the high-level directive ``hzResourceTable`` that replaces common
templates so we do not need to write boilerplate HTML and controller code. It
gives developers a quick way to build a new table or change an existing table.

.. note::

    You may still choose to use the HTML template for complete control of form
    and functionality. For example, you may want to create a custom footer.
    You may also use the ``hzDynamicTable`` directive (what ``hzResourceTable``
    uses under the hood) directly. However, neither of these is extensible.
    You would need to override the panel completely.

This is a sample module file to demonstrate how to make some customizations to
the Images Panel.::

    (function() {
      'use strict';

      angular
        .module('horizon.app.core.images')
        .run(customizeImagePanel);

      customizeImagePanel.$inject = [
        'horizon.framework.conf.resource-type-registry.service',
        'horizon.app.core.images.basePath',
        'horizon.app.core.images.resourceType',
        'horizon.app.core.images.actions.surprise.service'
      ];

      function customizeImagePanel(registry, basePath, imageResourceType, surpriseService) {
        // get registry for ``OS::Glance::Image``
        registry = registry.getResourceType(imageResourceType);

        // replace existing Size column to make the font color red
        var column = {
          id: 'size',
          priority: 2,
          template: '<a style="color:red;">{$ item.size | bytes $}</a>'
        };
        registry.tableColumns.replace('size', column);

        // add a new detail view
        registry.detailsViews
          .append({
            id: 'anotherDetailView',
            name: gettext('Another Detail View'),
            template: basePath + 'demo/detail.html'
        });

        // set a different summary drawer template
        registry.setSummaryTemplateUrl(basePath + 'demo/drawer.html');

        // add a new global action
        registry.globalActions
          .append({
            id: 'surpriseAction',
            service: surpriseService,
            template: {
              text: gettext('Surprise')
            }
        });
      }
    })();

Additionally, you should have content defined in ``detail.html`` and
``drawer.html``, as well as define the ``surpriseService`` which is based off
the ``actions`` directive and needs allowed and perform methods defined.


Icons
=====

Horizon uses font icons from Font Awesome.  Please see `Font Awesome`_ for
instructions on how to use icons in the code.

To add icon to Table Action, use icon property. Example:

.. code-block:: python

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
template ``openstack_dashboard/templates/base.html`` defines multiple blocks
that can be overridden.

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
``openstack_dashboard/dashboards/my_custom_dashboard/static/my_custom_dashboard/scss/my_custom_dashboard.scss``.

All dashboard's templates have to inherit from dashboard's base.html::

    {% extends 'my_custom_dashboard/base.html' %}
    ...


Custom Javascript
=================

Similarly to adding custom styling (see above), it is possible to include
custom javascript files.

All Horizon's javascript files are listed in the
``openstack_dashboard/templates/horizon/_scripts.html``
partial template, which is included in Horizon's base template in ``block js``.

To add custom javascript files, create an ``_scripts.html`` partial template in
your dashboard
``openstack_dashboard/dashboards/my_custom_dashboard/templates/my_custom_dashboard/_scripts.html``
which extends ``horizon/_scripts.html``. In this template override the
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

Custom Head js
--------------

Additionally, some scripts require you to place them within the page's <head>
tag. To do this, recursively extend the ``base.html`` template in your theme
to override the ``custom_head_js`` block.

Your theme's ``base.html``::

    {% extends "base.html" %}

    {% block custom_head_js %}
      <script src='{{ STATIC_URL }}/my_custom_dashboard/js/my_custom_js.js' type='text/javascript' charset='utf-8'></script>
    {% endblock %}

See the ``example`` theme for a working theme that uses these blocks.

.. warning::

    Don't use the ``custom_head_js`` block for analytics tracking. See below.

Custom Analytics
----------------

For analytics or tracking scripts you should avoid the ``custom_head_js``
block. We have a specific block instead called ``custom_analytics``. Much like
the ``custom_head_js`` block this inserts additional content into the head of
the ``base.html`` template and it will be on all pages.

The reason for an analytics specific block is that for security purposes we
want to be able to turn off tracking on certain pages that we deem sensitive.
This is done for the safety of the users and the cloud admins. By using this
block instead, pages using ``base.html`` can override it themselves when they
want to avoid tracking. They can't simply override the custom js because it may
be non-tracking code.

Your theme's ``base.html``::

    {% extends "base.html" %}

    {% block custom_analytics %}
      <script src='{{ STATIC_URL }}/my_custom_dashboard/js/my_tracking_js.js' type='text/javascript' charset='utf-8'></script>
    {% endblock %}

See the ``example`` theme for a working theme that uses these blocks.

Customizing Meta Attributes
===========================

To add custom metadata attributes to your project's base template use the
``custom_metadata`` block. To do this, recursively extend the ``base.html``
template in your theme to override the ``custom_metadata`` block. The contents
of this block will be inserted into the page's <head> just after the default
Horizon meta tags.

Your theme's ``base.html``::

    {% extends "base.html" %}

    {% block custom_metadata %}
      <meta name="description" content="My custom metadata.">
    {% endblock %}

See the ``example`` theme for a working theme that uses these blocks.

..  _Font Awesome: https://fortawesome.github.io/Font-Awesome/
