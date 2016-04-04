==============
Horizon Plugin
==============

Why should I package my code as a plugin?
=========================================

We highly encourage that you write and maintain your code using our plugin
architecture. A plugin by definition means the ability to be connected. In
practical terms, plugins are a way to extend and add to the functionality that
already exists. You can control its content and progress at a rate independent
of Horizon. If you write and package your code as a plugin, it will continue to
work in future releases.

Writing your code as a plugin also modularizes your code making it easier to
translate and test. This also makes it easier for deployers to consume your code
allowing selective enablement of features. We are currently using this pattern
internally for our dashboards.

Creating the Plugin
===================

This tutorial assumes you have a basic understanding of Python, HTML,
JavaScript. Knowledge of AngularJS is optional but recommended if you are
attempting to create an Angular plugin.

Types of Plugins that add content
---------------------------------

The file structure for your plugin type will be different depending on your
needs. Your plugin can be categorized into two types:

* Plugins that create new panels or dashboards
* Plugins that modify existing workflows, actions, etc... (Angular only)

We will cover the basics of working with panels for both Python and Angular.
If you are interested in creating a new panel, follow the steps below.

..  Note ::

    This tutorial shows you how to create a new panel. If you are interested in
    creating a new dashboard plugin, use the file structure from
    :doc:`Tutorial: Building a Dashboard using Horizon </tutorials/dashboard>`
    instead.

File Structure
--------------
Below is a skeleton of what your plugin should look like.::

  myplugin
  │
  ├── myplugin
  │   ├── __init__.py
  │   │
  │   ├── enabled
  │   │   └──_31000_myplugin.py
  │   │
  │   ├── api
  │   │   ├──__init__.py
  │   │   ├── my_rest_api.py
  │   │   └── myservice.py
  │   │
  │   ├── content
  │   │   ├──__init__.py
  │   │   └── mypanel
  │   │       ├── __init__.py
  │   │       ├── panel.py
  │   │       ├── tests.py
  │   │       ├── urls.py
  │   │       ├── views.py
  │   │       └── templates
  │   │           └── mypanel
  │   │               └── index.html
  │   │
  │   └── static
  │       └── dashboard
  │           └── identity
  │               └── myplugin
  │                   └── mypanel
  │                       ├── mypanel.html
  │                       ├── mypanel.js
  │                       └── mypanel.scss
  ├── setup.py
  ├── setup.cfg
  ├── LICENSE
  ├── MANIFEST.in
  └── README.rst

If you are creating a Python plugin, you may ignore the ``static`` folder. Most
of the classes you need are provided for in Python. If you intend on adding
custom front-end logic, you will need to include additional JavaScript here.

An AngularJS plugin is a collection of JavaScript files or static resources.
Because it runs entirely in your browser, we need to place all of our static
resources inside the ``static`` folder. This ensures that the Django static
collector picks it up and distributes it to the browser correctly.

The Enabled File
----------------

The enabled folder contains the configuration file(s) that registers your
plugin with Horizon. The file is prefixed with an alpha-numberic string that
determines the load order of your plugin. For more information on what you can
include in this file, see pluggable settings in
:doc:`Settings and Configuration </topics/settings>`

_31000_myplugin.py::

    # The name of the panel to be added to HORIZON_CONFIG. Required.
    PANEL = 'mypanel'

    # The name of the dashboard the PANEL associated with. Required.
    PANEL_DASHBOARD = 'identity'

    # Python panel class of the PANEL to be added.
    ADD_PANEL = 'myplugin.content.mypanel.panel.MyPanel'

    # A list of applications to be prepended to INSTALLED_APPS
    ADD_INSTALLED_APPS = ['myplugin']

    # A list of AngularJS modules to be loaded when Angular bootstraps.
    ADD_ANGULAR_MODULES = ['horizon.dashboard.identity.myplugin.mypanel']

    # Automatically discover static resources in installed apps
    AUTO_DISCOVER_STATIC_FILES = True

    # A list of js files to be included in the compressed set of files
    ADD_JS_FILES = []

    # A list of scss files to be included in the compressed set of files
    ADD_SCSS_FILES = ['dashboard/identity/myplugin/myplugin.scss']

..  Note ::

  Currently, AUTO_DISCOVER_STATIC_FILES = True will only discover JavaScript files,
  not SCSS files.

my_rest_api.py
--------------

This file will likely be necessary if creating a plugin using Angular. Your
plugin will need to communicate with a new service or require new interactions
with a service already supported by Horizon. In this particular example, the
plugin will augment the support for the already supported Identity service,
Keystone. This file serves to define new REST interfaces for the plugin's
clientside to communicate with Horizon. Typically, the REST interfaces here
make calls into ``myservice.py``.

This file is unnecessary in a purely Django based plugin, or if your Angular
based plugin is relying on CORS support in the desired service. For more
information on CORS, see
`http://docs.openstack.org/admin-guide-cloud/cross_project_cors.html`

myservice.py
------------

This file will likely be necessary if creating a Django or Angular driven
plugin. This file is intended to act as a convenient location for interacting
with the new service this plugin is supporting. While interactions with the
service can be handled in the ``views.py``, isolating the logic is an
established pattern in Horizon.

panel.py
--------

We define a panel where our plugin's content will reside in. This is currently a
neccessity even for Angular plugins. The slug is the panel's unique identifier
and is often use as part of the URL. Make sure that it matches what you have in
your enabled file.::

    from django.utils.translation import ugettext_lazy as _
    import horizon


    class MyPanel(horizon.Panel):
        name = _("My Panel")
        slug = "mypanel"

tests.py
--------

Write some tests for the Django portion of your plugin and place them here.

urls.py
-------

Now that we have a panel, we need to provide a URL so that users can visit our
new panel! This URL generally will point to a view.::

    from django.conf.urls import url

    from myplugin.content.mypanel import views

    urlpatterns = [
        url(r'^$', views.IndexView.as_view(), name='index'),
    ]

views.py
--------

Because rendering is done client-side, all our view needs is to reference some
HTML page. If you are writing a Python plugin, this view can be much more
complex. Refer to the topic guides for more details.::

    from django.views import generic


    class IndexView(generic.TemplateView):
        template_name = 'identity/mypanel/index.html'

index.html
----------

The index HTML is where rendering occurs. In this example, we are only using
Django. If you are interested in using Angular directives instead, read the
AngularJS section below.::

    {% extends 'base.html' %}
    {% load i18n %}
    {% block title %}{% trans "My plugin" %}{% endblock %}

    {% block page_header %}
      {% include "horizon/common/_domain_page_header.html"
        with title=_("My Panel") %}
    {% endblock page_header %}

    {% block main %}
      Hello world!
    {% endblock %}

At this point, you have a very basic plugin. Note that new templates are
required to extend base.html. Including base.html is important for a number of
reasons. It is the template that contains all of your static resources along
with any functionality external to your panel (things like navigation, context
selection, etc...). As of this moment, this is also true for Angular plugins.

MANIFEST.in
-----------
This file is responsible for listing the paths you want included in your tar.::

    include setup.py

    recursive-include myplugin *.js *.html *.scss


setup.py
--------
::

    # THIS FILE IS MANAGED BY THE GLOBAL REQUIREMENTS REPO - DO NOT EDIT
    import setuptools

    # In python < 2.7.4, a lazy loading of package `pbr` will break
    # setuptools if some other modules registered functions in `atexit`.
    # solution from: http://bugs.python.org/issue15881#msg170215
    try:
        import multiprocessing  # noqa
    except ImportError:
        pass

    setuptools.setup(
        setup_requires=['pbr>=1.8'],
        pbr=True)

setup.cfg
---------
::

    [metadata]
    name = myplugin
    version = 0.0.1
    summary = A panel plugin for OpenStack Dashboard
    description-file =
        README.rst
    author = myname
    author_email = myemail
    home-page = http://www.openstack.org/
    classifiers = [
        Environment :: OpenStack
        Framework :: Django
        Intended Audience :: Developers
        Intended Audience :: System Administrators
        License :: OSI Approved :: Apache Software License
        Operating System :: POSIX :: Linux
        Programming Language :: Python
        Programming Language :: Python :: 2
        Programming Language :: Python :: 2.7
        Programming Language :: Python :: 3.4

    [files]
    packages =
        myplugin

AngularJS Plugin
================

If you have no plans to add AngularJS to your plugin, you may skip this section.
In the tutorial below, we will show you how to customize your panel using
Angular.

index.html
----------

The index HTML is where rendering occurs and serves as an entry point for
Angular. This is where we start to diverge from the traditional Python plugin.
In this example, we use a Django template as the glue to our Angular template.
Why are we going through a Django template for an Angular plugin? Long story
short, ``base.html`` contains the navigation piece that we still need for each
panel.

::

    {% extends 'base.html' %}
    {% load i18n %}
    {% block title %}{% trans "My panel" %}{% endblock %}

    {% block page_header %}
      <hz-page-header
        header="{$ 'My panel' | translate $}"
        description="{$ 'My custom panel!' | translate $}">
      </hz-page-header>
    {% endblock page_header %}

    {% block main %}
      <ng-include
        src="'{{ STATIC_URL }}dashboard/identity/myplugin/mypanel/mypanel.html'">
      </ng-include>
    {% endblock %}

This template contains both Django and AngularJS code. Angular is denoted by
{$..$} while Django is denoted by {{..}} and {%..%}. This template gets
processed twice, once by Django on the server-side and once more by Angular on
the client-side. This means that the expressions in {{..}} and {%..%} are
substituted with values by the time it reaches your Angular template.

What you chose to include in ``block main`` is entirely up to you. Since you are
creating an Angular plugin, we recommend that you keep everything in this
section Angular. Do not mix Python code in here! If you find yourself passing in
Python data, do it via our REST services instead.

Remember to always use ``STATIC_URL`` when referencing your static resources.
This ensures that changes to the static path in settings will continue to serve
your static resources properly.

..  Note ::

    Angular's directives are prefixed with ng. Similarly, Horizon's directives
    are prefixed with hz. You can think of them as namespaces.

mypanel.js
-----------

Your controller is the glue between the model and the view. In this example, we
are going to give it some fake data to render. To load more complex data,
consider using the $http service.

::

    (function() {
      'use strict';

      angular
        .module('horizon.dashboard.identity.myplugin.mypanel', [])
        .controller('horizon.dashboard.identity.myPluginController',
          myPluginController);

      myPluginController.$inject = [ '$http' ];

      function myPluginController($http) {
        var ctrl = this;
        ctrl.items = [
          { name: 'abc', id: 123 },
          { name: 'efg', id: 345 },
          { name: 'hij', id: 678 }
        ];
      }
    })();

This is a basic example where we mocked the data. For exercise, load your data
using the ``$http`` service.

mypanel.html
-------------

This is our view. In this example, we are looping through the list of items
provided by the controller and displaying the name and id. The important thing
to note is the reference to our controller using the ``ng-controller``
directive.

::

    <div ng-controller="horizon.dashboard.identity.myPluginController as ctrl">
      <div>Loading data from your controller:</div>
      <ul>
        <li ng-repeat="item in ctrl.items">
          <span class="c1">{$ item.name $}</span>
          <span class="c2">{$ item.id $}</span>
        </li>
      </ul>
    </div>

mypanel.scss
-------------

You can choose to customize your panel by providing your own scss.
Be sure to include it in your enabled file via the ``ADD_SCSS_FILES`` setting.

Installing Your Plugin
======================

Now that you have a complete plugin, it is time to install and test it. The
instructions below assume that you have a working plugin.

* ``plugin`` is the location of your plugin
* ``horizon`` is the location of horizon
* ``package`` is the complete name of your packaged plugin

::

1. Run "cd ``plugin`` & python setup.py sdist"
2. Run "cp -rv enabled ``horizon``/openstack_dashboard/local/"
3. Run "``horizon``/tools/with_venv.sh pip install dist/``package``.tar.gz"
4. Restart Apache or your Django test server

..  Note ::

  Step 3 installs your package into the Horizon's virtual environment. You can
  install your plugin without using ``with_venv.sh`` and ``pip``. The package
  would simply be installed in the ``PYTHON_PATH`` of the system instead.

If you are able to hit the URL pattern in ``urls.py`` in your browser, you have
successfully deployed your plugin! For plugins that do not have a URL, check
that your static resources are loaded using the browser inspector.

Assuming you implemented ``my_rest_api.py``, you can use a REST client to hit
the url directly and test it. There should be many REST clients available on
your web browser.

Note that you may need to rebuild your virtual environment if your plugin is not
showing up properly. If your plugin does not show up properly, check your
``.venv`` folder to make sure the plugin's content is as you expect.

..  Note ::

  To uninstall, use ``pip uninstall``. You will also need to remove the enabled
  file from the ``local/enabled`` folder.
