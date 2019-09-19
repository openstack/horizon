.. _install-settings:

==================
Settings Reference
==================

Introduction
============

Horizon's settings broadly fall into four categories:

* `General Settings`_: this includes visual settings like the modal backdrop
  style, bug url and theme configuration, as well as settings that affect every
  service, such as page sizes on API requests.
* `Service-specific Settings`_: Many services that Horizon consumes, such
  as Nova and Neutron, don't advertise their capabilities via APIs, so Horizon
  carries configuration for operators to enable or disable many items. This
  section covers all settings that are specific to a single service.
* `Django Settings`_, which are common to all Django applications. The only
  ones documented here are those that Horizon alters by default; however, you
  should read the `Django settings documentation
  <https://docs.djangoproject.com/en/dev/topics/settings/>`_ to see the other
  options available to you.
* `Other Settings`_: settings which do not fall into any of the above
  categories.

To modify your settings, you have two options:

* **Preferred:** Add ``.py`` settings snippets to the
  ``openstack_dashboard/local/local_settings.d/`` directory. Several example
  files (appended with ``.example``) can be found there. These must start
  with an underscore, and are evaluated alphabetically, after
  ``local_settings.py``.
* Modify your ``openstack_dashboard/local/local_settings.py``. There is an
  file found at ``openstack_dashboard/local/local_settings.py.example``.

General Settings
================

.. _angular_features:

ANGULAR_FEATURES
----------------

.. versionadded:: 10.0.0(Newton)

Default:

.. code-block:: python

    {
        'images_panel': True,
        'key_pairs_panel': True,
        'flavors_panel': False,
        'domains_panel': False,
        'users_panel': False,
        'groups_panel': False,
        'roles_panel': True
    }

A dictionary of currently available AngularJS features. This allows simple
toggling of legacy or rewritten features, such as new panels, workflows etc.

.. note::

    If you toggle ``domains_panel`` to ``True``, you also need to enable the
    setting of `OPENSTACK_KEYSTONE_DEFAULT_DOMAIN`_ and add
    `OPENSTACK_KEYSTONE_DEFAULT_DOMAIN`_ to `REST_API_REQUIRED_SETTINGS`_.

API_RESULT_LIMIT
----------------

.. versionadded:: 2012.1(Essex)

Default: ``1000``

The maximum number of objects (e.g. Swift objects or Glance images) to display
on a single page before providing a paging element (a "more" link) to paginate
results.

API_RESULT_PAGE_SIZE
--------------------

.. versionadded:: 2012.2(Folsom)

Default: ``20``

Similar to ``API_RESULT_LIMIT``. This setting controls the number of items
to be shown per page if API pagination support for this exists.

.. _available_themes:

AVAILABLE_THEMES
----------------

.. versionadded:: 9.0.0(Mitaka)

Default:

.. code-block:: python

   AVAILABLE_THEMES = [
        ('default', 'Default', 'themes/default'),
        ('material', 'Material', 'themes/material'),
   ]

This setting tells Horizon which themes to use.

A list of tuples which define multiple themes. The tuple format is
``('{{ theme_name }}', '{{ theme_label }}', '{{ theme_path }}')``.

The ``theme_name`` is the name used to define the directory which
the theme is collected into, under ``/{{ THEME_COLLECTION_DIR }}``.
It also specifies the key by which the selected theme is stored in
the browser's cookie.

The ``theme_label`` is the user-facing label that is shown in the
theme picker.  The theme picker is only visible if more than one
theme is configured, and shows under the topnav's user menu.

By default, the ``theme path`` is the directory that will serve as
the static root of the theme and the entire contents of the directory
is served up at ``/{{ THEME_COLLECTION_DIR }}/{{ theme_name }}``.
If you wish to include content other than static files in a theme
directory, but do not wish that content to be served up, then you
can create a sub directory named ``static``. If the theme folder
contains a sub-directory with the name ``static``, then
``static/custom/static`` will be used as the root for the content
served at ``/static/custom``.

The static root of the theme folder must always contain a _variables.scss
file and a _styles.scss file.  These must contain or import all the
bootstrap and horizon specific variables and styles which are used to style
the GUI. For example themes, see: /horizon/openstack_dashboard/themes/

Horizon ships with two themes configured. 'default' is the default theme,
and 'material' is based on Google's Material Design.

DEFAULT_THEME
-------------

.. versionadded:: 9.0.0(Mitaka)

Default: ``"default"``

This setting tells Horizon which theme to use if the user has not
yet selected a theme through the theme picker and therefore set the
cookie value. This value represents the ``theme_name`` key that is
used from `AVAILABLE_THEMES`_.  To use this setting, the theme must
also be configured inside of ``AVAILABLE_THEMES``. Your default theme
must be configured as part of `SELECTABLE_THEMES`_.  If it is not, then
your ``DEFAULT_THEME`` will default to the first theme in
``SELECTABLE_THEMES``.

DISALLOW_IFRAME_EMBED
---------------------

.. versionadded:: 8.0.0(Liberty)

Default: ``True``

This setting can be used to defend against Clickjacking and prevent Horizon from
being embedded within an iframe. Legacy browsers are still vulnerable to a
Cross-Frame Scripting (XFS) vulnerability, so this option allows extra security
hardening where iframes are not used in deployment. When set to true, a
``"frame-buster"`` script is inserted into the template header that prevents the
web page from being framed and therefore defends against clickjacking.

For more information see: http://tinyurl.com/anticlickjack

.. note::

  If your deployment requires the use of iframes, you can set this setting to
  ``False`` to exclude the frame-busting code and allow iframe embedding.

DROPDOWN_MAX_ITEMS
------------------

.. versionadded:: 2015.1(Kilo)

Default: ``30``

This setting sets the maximum number of items displayed in a dropdown.
Dropdowns that limit based on this value need to support a way to observe
the entire list.

FILTER_DATA_FIRST
-----------------

.. versionadded:: 10.0.0(Newton)

Default:

.. code-block:: python

    {
        'admin.instances': False,
        'admin.images': False,
        'admin.networks': False,
        'admin.routers': False,
        'admin.volumes': False
    }

If the dict key-value is True, when the view loads, an empty table will be
rendered and the user will be asked to provide a search criteria first (in case
no search criteria was provided) before loading any data.

Examples:

Override the dict:

.. code-block:: python

    {
        'admin.instances': True,
        'admin.images': True,
        'admin.networks': False,
        'admin.routers': False,
        'admin.volumes': False
    }

Or, if you want to turn this on for an specific panel/view do:

.. code-block:: python

    FILTER_DATA_FIRST['admin.instances'] = True

HORIZON_CONFIG
--------------

A dictionary of some Horizon configuration values. These are primarily
separated for historic design reasons.

Default:

.. code-block:: python

    HORIZON_CONFIG = {
        'user_home': 'openstack_dashboard.views.get_user_home',
        'ajax_queue_limit': 10,
        'auto_fade_alerts': {
            'delay': 3000,
            'fade_duration': 1500,
            'types': [
                'alert-success',
                'alert-info'
            ]
        },
        'bug_url': None,
        'help_url': "https://docs.openstack.org/",
        'exceptions': {
            'recoverable': exceptions.RECOVERABLE,
            'not_found': exceptions.NOT_FOUND,
            'unauthorized': exceptions.UNAUTHORIZED
        },
        'modal_backdrop': 'static',
        'angular_modules': [],
        'js_files': [],
        'js_spec_files': [],
        'external_templates': [],
    }

ajax_poll_interval
~~~~~~~~~~~~~~~~~~

.. versionadded:: 2012.1(Essex)

Default: ``2500``

How frequently resources in transition states should be polled for updates,
expressed in milliseconds.

ajax_queue_limit
~~~~~~~~~~~~~~~~

.. versionadded:: 2012.1(Essex)

Default: ``10``

The maximum number of simultaneous AJAX connections the dashboard may try
to make. This is particularly relevant when monitoring a large number of
instances, volumes, etc. which are all actively trying to update/change state.

angular_modules
~~~~~~~~~~~~~~~

.. versionadded:: 2014.2(Juno)

Default: ``[]``

A list of AngularJS modules to be loaded when Angular bootstraps. These modules
are added as dependencies on the root Horizon application ``horizon``.

auto_fade_alerts
~~~~~~~~~~~~~~~~

.. versionadded:: 2013.2(Havana)

Default:

.. code-block:: python

    {
        'delay': 3000,
        'fade_duration': 1500,
        'types': []
    }

If provided, will auto-fade the alert types specified. Valid alert types
include: ['alert-default', 'alert-success', 'alert-info', 'alert-warning',
'alert-danger']  Can also define the delay before the alert fades and the fade
out duration.

bug_url
~~~~~~~

.. versionadded:: 9.0.0(Mitaka)

Default: ``None``

If provided, a "Report Bug" link will be displayed in the site header which
links to the value of this setting (ideally a URL containing information on
how to report issues).

disable_password_reveal
~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2015.1(Kilo)

Default: ``False``

Setting this to True will disable the reveal button for password fields,
including on the login form.

exceptions
~~~~~~~~~~

.. versionadded:: 2012.1(Essex)

Default:

.. code-block:: python

    {
        'unauthorized': [],
        'not_found': [],
        'recoverable': []
    }

A dictionary containing classes of exceptions which Horizon's centralized
exception handling should be aware of. Based on these exception categories,
Horizon will handle the exception and display a message to the user.

help_url
~~~~~~~~

.. versionadded:: 2012.2(Folsom)

Default: ``None``

If provided, a "Help" link will be displayed in the site header which links
to the value of this setting (ideally a URL containing help information).

js_files
~~~~~~~~

.. versionadded:: 2014.2(Juno)

Default: ``[]``

A list of javascript source files to be included in the compressed set of files
that are loaded on every page. This is needed for AngularJS modules that are
referenced in ``angular_modules`` and therefore need to be include in every
page.

js_spec_files
~~~~~~~~~~~~~

.. versionadded:: 2015.1(Kilo)

Default: ``[]``

A list of javascript spec files to include for integration with the Jasmine
spec runner. Jasmine is a behavior-driven development framework for testing
JavaScript code.

modal_backdrop
~~~~~~~~~~~~~~

.. versionadded:: 2014.2(Kilo)

Default: ``"static"``

Controls how bootstrap backdrop element outside of modals looks and feels.
Valid values are ``"true"`` (show backdrop element outside the modal, close
the modal after clicking on backdrop), ``"false"`` (do not show backdrop
element, do not close the modal after clicking outside of it) and ``"static"``
(show backdrop element outside the modal, do not close the modal after
clicking on backdrop).

password_autocomplete
~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2013.1(Grizzly)

Default: ``"off"``

Controls whether browser autocompletion should be enabled on the login form.
Valid values are ``"on"`` and ``"off"``.

password_validator
~~~~~~~~~~~~~~~~~~

.. versionadded:: 2012.1(Essex)

Default:

.. code-block:: python

    {
        'regex': '.*',
        'help_text': _("Password is not accepted")
    }

A dictionary containing a regular expression which will be used for password
validation and help text which will be displayed if the password does not
pass validation. The help text should describe the password requirements if
there are any.

This setting allows you to set rules for passwords if your organization
requires them.

user_home
~~~~~~~~~

.. versionadded:: 2012.1(Essex)

Default: ``settings.LOGIN_REDIRECT_URL``

This can be either a literal URL path (such as the default), or Python's
dotted string notation representing a function which will evaluate what URL
a user should be redirected to based on the attributes of that user.

MESSAGES_PATH
-------------

.. versionadded:: 9.0.0(Mitaka)

Default: ``None``

The absolute path to the directory where message files are collected.

When the user logins to horizon, the message files collected are processed
and displayed to the user. Each message file should contain a JSON formatted
data and must have a .json file extension. For example:

.. code-block:: python

    {
        "level": "info",
        "message": "message of the day here"
    }

Possible values for level are: ``success``, ``info``, ``warning`` and
``error``.

NG_TEMPLATE_CACHE_AGE
---------------------

.. versionadded:: 10.0.0(Newton)

Angular Templates are cached using this duration (in seconds) if `DEBUG`_
is set to ``False``.  Default value is ``2592000`` (or 30 days).

OPENSTACK_API_VERSIONS
----------------------

.. versionadded:: 2013.2(Havana)

Default:

.. code-block:: python

    {
        "identity": 3,
        "volume": 3,
        "compute": 2
    }

Overrides for OpenStack API versions. Use this setting to force the
OpenStack dashboard to use a specific API version for a given service API.

.. note::

    The version should be formatted as it appears in the URL for the
    service API. For example, the identity service APIs have inconsistent
    use of the decimal point, so valid options would be "3".
    For example:

    .. code-block:: python

        OPENSTACK_API_VERSIONS = {
            "identity": 3,
            "volume": 3,
            "compute": 2
        }

OPENSTACK_CLOUDS_YAML_CUSTOM_TEMPLATE
-------------------------------------

.. versionadded:: 15.0.0(Stein)

Default: ``None``

Example:: ``my-clouds.yaml.template``

A template name for a custom user's ``clouds.yaml`` file.
``None`` means the default template for ``clouds.yaml`` is used.

If the default template is not suitable for your deployment,
you can provide your own clouds.yaml by specifying this setting.

The default template is defined as `clouds.yaml.template
<https://opendev.org/openstack/horizon/src/branch/master/openstack_dashboard/dashboards/project/api_access/templates/api_access/clouds.yaml.template>`__
and available context parameters are found in ``_get_openrc_credentials()``
and ``download_clouds_yaml_file()`` functions in
`openstack_dashboard/dashboards/project/api_access/views.py
<https://opendev.org/openstack/horizon/src/branch/master/openstack_dashboard/dashboards/project/api_access/views.py>`__.

.. note::

   Your template needs to be placed in the search paths of Django templates.
   You may need to configure `ADD_TEMPLATE_DIRS`_ setting
   to contain a path where your template exists.

OPENSTACK_CLOUDS_YAML_NAME
--------------------------

.. versionadded:: 12.0.0(Pike)

Default: ``"openstack"``

The name of the entry to put into the user's clouds.yaml file.

OPENSTACK_CLOUDS_YAML_PROFILE
-----------------------------

.. versionadded:: 12.0.0(Pike)

Default: ``None``

If set, the name of the `vendor profile`_ from `os-client-config`_.

.. _vendor profile: https://docs.openstack.org/os-client-config/latest/user/vendor-support.html
.. _os-client-config: https://docs.openstack.org/os-client-config/latest/

OPENSTACK_ENDPOINT_TYPE
-----------------------

.. versionadded:: 2012.1(Essex)

Default: ``"publicURL"``

A string which specifies the endpoint type to use for the endpoints in the
Keystone service catalog. The default value for all services except for
identity is ``"publicURL"`` . The default value for the identity service is
``"internalURL"``.

OPENSTACK_HOST
--------------

.. versionadded:: 2012.1(Essex)

Default: ``"127.0.0.1"``

The hostname of the Keystone server used for authentication if you only have
one region. This is often the **only** setting that needs to be set for a
basic deployment.

If you have multiple regions you should use the `AVAILABLE_REGIONS`_ setting
instead.

OPENRC_CUSTOM_TEMPLATE
----------------------

.. versionadded:: 15.0.0(Stein)

Default: ``None``

Example:: ``my-openrc.sh.template``

A template name for a custom user's ``openrc`` file.
``None`` means the default template for ``openrc`` is used.

If the default template is not suitable for your deployment,
for example, if your deployment uses saml2, openid and so on
for authentication, the default ``openrc`` would not be sufficient.
You can provide your own clouds.yaml by specifying this setting.

The default template is defined as `openrc.sh.template
<https://opendev.org/openstack/horizon/src/branch/master/openstack_dashboard/dashboards/project/api_access/templates/api_access/openrc.sh.template>`__
and available context parameters are found in ``_get_openrc_credentials()``
and ``download_rc_file()`` functions in
`openstack_dashboard/dashboards/project/api_access/views.py
<https://opendev.org/openstack/horizon/src/branch/master/openstack_dashboard/dashboards/project/api_access/views.py>`__.

.. note::

   Your template needs to be placed in the search paths of Django templates.
   Check ``TEMPLATES[0]['DIRS']``.
   You may need to specify somewhere your template exist
   to ``DIRS`` in ``TEMPLATES`` setting.

OPENSTACK_PROFILER
------------------

.. versionadded:: 11.0.0(Ocata)

Default: ``{"enabled": False}``

Various settings related to integration with osprofiler library. Since it is a
developer feature, it starts as disabled. To enable it, more than a single
``"enabled"`` key should be specified. Additional keys that should be specified
in that dictionary are:

* ``"keys"`` is a list of strings, which are secret keys used to encode/decode
  the profiler data contained in request headers. Encryption is used for
  security purposes, other OpenStack components that are expected to profile
  themselves with osprofiler using the data from the request that Horizon
  initiated must share a common set of keys with the ones in Horizon
  config. List of keys is used so that security keys could be changed in
  non-obtrusive manner for every component in the cloud.
  Example: ``"keys": ["SECRET_KEY", "MORE_SECRET_KEY"]``.
  For more details see `osprofiler documentation`_.
* ``"notifier_connection_string"`` is a url to which trace messages are sent by
  Horizon. For other components it is usually the only URL specified in config,
  because other components act mostly as traces producers. Example:
  ``"notifier_connection_string": "mongodb://%s" % OPENSTACK_HOST``.
* ``"receiver_connection_string"`` is a url from which traces are retrieved by
  Horizon, needed because Horizon is not only the traces producer, but also a
  consumer. Having 2 settings which usually contain the same value is legacy
  feature from older versions of osprofiler when OpenStack components could use
  oslo.messaging for notifications and the trace client used ceilometer as a
  receiver backend. By default Horizon uses the same URL pointing to a MongoDB
  cluster for both purposes, since ceilometer was too slow for using with UI.
  Example: ``"receiver_connection_string": "mongodb://%s" % OPENSTACK_HOST``.

.. _osprofiler documentation: https://docs.openstack.org/osprofiler/latest/user/integration.html#how-to-initialize-profiler-to-get-one-trace-across-all-services

OPENSTACK_SSL_CACERT
--------------------

.. versionadded:: 2013.2(Havana)

Default: ``None``

When unset or set to ``None`` the default CA certificate on the system is used
for SSL verification.

When set with the path to a custom CA certificate file, this overrides use of
the default system CA certificate. This custom certificate is used to verify all
connections to openstack services when making API calls.

OPENSTACK_SSL_NO_VERIFY
-----------------------

.. versionadded:: 2012.2(Folsom)

Default: ``False``

Disable SSL certificate checks in the OpenStack clients (useful for self-signed
certificates).

OPERATION_LOG_ENABLED
---------------------

.. versionadded:: 10.0.0(Newton)

Default: ``False``

This setting can be used to enable logging of all operations carried out by
users of Horizon. The format of the logs is configured via
`OPERATION_LOG_OPTIONS`_

.. note::

  If you use this feature, you need to configure the logger setting like
  an outputting path for operation log in ``local_settings.py``.

OPERATION_LOG_OPTIONS
---------------------

.. versionadded:: 10.0.0(Newton)

.. versionchanged:: 12.0.0(Pike)

    Added ``ignored_urls`` parameter and added ``%(client_ip)s`` to ``format``

Default:

.. code-block:: python

    {
        'mask_fields': ['password'],
        'target_methods': ['POST'],
        'ignored_urls': ['/js/', '/static/', '^/api/'],
        'format': ("[%(domain_name)s] [%(domain_id)s] [%(project_name)s]"
            " [%(project_id)s] [%(user_name)s] [%(user_id)s] [%(request_scheme)s]"
            " [%(referer_url)s] [%(request_url)s] [%(message)s] [%(method)s]"
            " [%(http_status)s] [%(param)s]"),
    }

This setting controls the behavior of the operation log.

* ``mask_fields`` is a list of keys of post data which should be masked from the
  point of view of security. Fields like ``password`` should be included.
  The fields specified in ``mask_fields`` are logged as ``********``.
* ``target_methods`` is a request method which is logged to an operation log.
  The valid methods are ``POST``, ``GET``, ``PUT``, ``DELETE``.
* ``ignored_urls`` is a list of request URLs to be hidden from a log.
* ``format`` defines the operation log format.
  Currently you can use the following keywords.
  The default value contains all keywords.

  * ``%(client_ip)s``
  * ``%(domain_name)s``
  * ``%(domain_id)s``
  * ``%(project_name)s``
  * ``%(project_id)s``
  * ``%(user_name)s``
  * ``%(user_id)s``
  * ``%(request_scheme)s``
  * ``%(referer_url)s``
  * ``%(request_url)s``
  * ``%(message)s``
  * ``%(method)s``
  * ``%(http_status)s``
  * ``%(param)s``

OVERVIEW_DAYS_RANGE
-------------------

.. versionadded:: 10.0.0(Newton)

Default:: ``1``

When set to an integer N (as by default), the start date in the Overview panel
meters will be today minus N days. This setting is used to limit the amount of
data fetched by default when rendering the Overview panel. If set to ``None``
(which corresponds to the behavior in past Horizon versions), the start date
will be from the beginning of the current month until the current date. The
legacy behaviour is not recommended for large deployments as Horizon suffers
significant lag in this case.

POLICY_CHECK_FUNCTION
---------------------

.. versionadded:: 2013.2(Havana)

Default:: ``openstack_auth.policy.check``

This value should not be changed, although removing it or setting it to
``None`` would be a means to bypass all policy checks.

POLICY_DIRS
-----------

.. versionadded:: 13.0.0(Queens)

Default:

.. code-block:: python

    {
        'compute': ['nova_policy.d'],
        'volume': ['cinder_policy.d'],
    }

Specifies a list of policy directories per service types. The directories
are relative to `POLICY_FILES_PATH`_. Services whose additional policies
are defined here must be defined in `POLICY_FILES`_ too. Otherwise,
additional policies specified in ``POLICY_DIRS`` are not loaded.

.. note::

   ``cinder_policy.d`` and ``nova_policy.d`` are registered by default
   to maintain policies which have ben dropped from nova and cinder
   but horizon still uses. We recommend not to drop them.

POLICY_FILES
------------

.. versionadded:: 2013.2(Havana)

Default:

.. code-block:: python

    {
        'compute': 'nova_policy.json',
        'identity': 'keystone_policy.json',
        'image': 'glance_policy.json',
        'network': 'neutron_policy.json',
        'volume': 'cinder_policy.json',
    }

This should essentially be the mapping of the contents of `POLICY_FILES_PATH`_
to service types. When policy.json files are added to `POLICY_FILES_PATH`_,
they should be included here too.

POLICY_FILES_PATH
-----------------

.. versionadded:: 2013.2(Havana)

Default:  ``os.path.join(ROOT_PATH, "conf")``

Specifies where service based policy files are located.  These are used to
define the policy rules actions are verified against.

REST_API_REQUIRED_SETTINGS
--------------------------

.. versionadded:: 2014.2(Kilo)

Default:

.. code-block:: python

    [
        'OPENSTACK_HYPERVISOR_FEATURES',
        'LAUNCH_INSTANCE_DEFAULTS',
        'OPENSTACK_IMAGE_FORMATS',
        'OPENSTACK_KEYSTONE_BACKEND',
        'OPENSTACK_KEYSTONE_DEFAULT_DOMAIN',
        'CREATE_IMAGE_DEFAULTS',
        'ENFORCE_PASSWORD_CHECK'
    ]

This setting allows you to expose configuration values over Horizons internal
REST API, so that the AngularJS panels can access them. Please be cautious
about which values are listed here (and thus exposed on the frontend).
For security purpose, this exposure of settings should be recognized explicitly
by operator. So ``REST_API_REQUIRED_SETTINGS`` is not set by default.
Please refer ``local_settings.py.example`` and confirm your ``local_settings.py``.

SELECTABLE_THEMES
---------------------

.. versionadded:: 12.0.0(Pike)

Default: ``AVAILABLE_THEMES``

This setting tells Horizon which themes to expose to the user as selectable
in the theme picker widget.  This value defaults to all themes configured
in `AVAILABLE_THEMES`_, but a brander may wish to simply inherit from an
existing theme and not allow that parent theme to be selected by the user.
``SELECTABLE_THEMES`` takes the exact same format as ``AVAILABLE_THEMES``.

SESSION_REFRESH
---------------

.. versionadded:: 15.0.0(Stein)

Default: ``True``

Control whether the SESSION_TIMEOUT period is refreshed due to activity. If
False, SESSION_TIMEOUT acts as a hard limit.

SESSION_TIMEOUT
---------------

.. versionadded:: 2013.2(Havana)

Default: ``"3600"``

This SESSION_TIMEOUT is a method to supercede the token timeout with a
shorter horizon session timeout (in seconds). If SESSION_REFRESH is True (the
default) SESSION_TIMEOUT acts like an idle timeout rather than being a hard
limit, but will never exceed the token expiry. If your token expires in 60
minutes, a value of 1800 will log users out after 30 minutes of inactivity,
or 60 minutes with activity. Setting SESSION_REFRESH to False will make
SESSION_TIMEOUT act like a hard limit on session times.


MEMOIZED_MAX_SIZE_DEFAULT
-------------------------

.. versionadded:: 15.0.0(Stein)

Default: ``"25"``

MEMOIZED_MAX_SIZE_DEFAULT allows setting a global default to help control
memory usage when caching. It should at least be 2 x the number of threads
with a little bit of extra buffer.

SHOW_OPENRC_FILE
----------------

.. versionadded:: 15.0.0(Stein)

Default:: ``True``

Controls whether the keystone openrc file is accesible from the user
menu and the api access panel.

.. seealso::

   `OPENRC_CUSTOM_TEMPLATE`_ to provide a custom ``openrc``.

SHOW_OPENSTACK_CLOUDS_YAML
--------------------------

.. versionadded:: 15.0.0(Stein)

Default:: ``True``

Controls whether clouds.yaml is accesible from the user
menu and the api access panel.

.. seealso::

   `OPENSTACK_CLOUDS_YAML_CUSTOM_TEMPLATE`_ to provide a custom
   ``clouds.yaml``.

THEME_COLLECTION_DIR
--------------------

.. versionadded:: 9.0.0(Mitaka)

Default: ``"themes"``

This setting tells Horizon which static directory to collect the
available themes into, and therefore which URL points to the theme
collection root.  For example, the default theme would be accessible
via ``/{{ STATIC_URL }}/themes/default``.

THEME_COOKIE_NAME
-----------------

.. versionadded:: 9.0.0(Mitaka)

Default: ``"theme"``

This setting tells Horizon in which cookie key to store the currently
set theme.  The cookie expiration is currently set to a year.

USER_MENU_LINKS
-----------------

.. versionadded:: 13.0.0(Queens)

Default:

.. code-block:: python

  [
    {'name': _('OpenStack RC File'),
     'icon_classes': ['fa-download', ],
     'url': 'horizon:project:api_access:openrc',
     'external': False,
     }
  ]

This setting controls the additional links on the user drop down menu.
A list of dictionaries defining all of the links should be provided. This
defaults to the standard OpenStack RC files.

Each dictionary should contain these values:

name
    The name of the link

url
    Either the reversible Django url name or an absolute url

external
    True for absolute URLs, False for django urls.

icon_classes
    A list of classes for the icon next to the link. If 'None' or
    an empty list is provided a download icon will show

WEBROOT
-------

.. versionadded:: 2015.1(Kilo)

Default: ``"/"``

Specifies the location where the access to the dashboard is configured in
the web server.

For example, if you're accessing the Dashboard via
``https://<your server>/dashboard``, you would set this to ``"/dashboard/"``.

.. note::

    Additional settings may be required in the config files of your webserver
    of choice. For example to make ``"/dashboard/"`` the web root in Apache,
    the ``"sites-available/horizon.conf"`` requires a couple of additional
    aliases set::

        Alias /dashboard/static %HORIZON_DIR%/static

        Alias /dashboard/media %HORIZON_DIR%/openstack_dashboard/static

    Apache also requires changing your WSGIScriptAlias to reflect the desired
    path.  For example, you'd replace ``/`` with ``/dashboard`` for the
    alias.



Service-specific Settings
=========================

The following settings inform the OpenStack Dashboard of information about the
other OpenStack projects which are part of this cloud and control the behavior
of specific dashboards, panels, API calls, etc.

Cinder
------

OPENSTACK_CINDER_FEATURES
~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2014.2(Juno)

Default: ``{'enable_backup': False}``

A dictionary of settings which can be used to enable optional services provided
by cinder.  Currently only the backup service is available.

Glance
------

CREATE_IMAGE_DEFAULTS
~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 12.0.0(Pike)

Default:

.. code-block:: python

    {
        'image_visibility': "public",
    }

A dictionary of default settings for create image modal.

The ``image_visibility`` setting specifies the default visibility option.
Valid values are  ``"public"`` and ``"private"``. By default, the visibility
option is public on create image modal. If it's set to ``"private"``, the
default visibility option is private.

HORIZON_IMAGES_UPLOAD_MODE
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 10.0.0(Newton)

Default: ``"legacy"``

Valid values are  ``"direct"``, ``"legacy"`` (default) and ``"off"``.
``"off"`` disables the ability to upload images via Horizon.
``legacy`` enables local file upload by piping the image file through the
Horizon's web-server. ``direct`` sends the image file directly from
the web browser to Glance. This bypasses Horizon web-server which both reduces
network hops and prevents filling up Horizon web-server's filesystem. ``direct``
is the preferred mode, but due to the following requirements it is not the
default. The ``direct`` setting requires a modern web browser, network access
from the browser to the public Glance endpoint, and CORS support to be enabled
on the Glance API service. Without CORS support, the browser will forbid the
PUT request to a location different than the Horizon server. To enable CORS
support for Glance API service, you will need to edit [cors] section of
glance-api.conf file (see `here`_ how to do it). Set `allowed_origin` to the
full hostname of Horizon web-server (e.g. http://<HOST_IP>/dashboard) and
restart glance-api process.

.. _here: https://docs.openstack.org/oslo.middleware/latest/reference/cors.html#configuration-for-oslo-config

IMAGE_CUSTOM_PROPERTY_TITLES
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2014.1(Icehouse)

Default:

.. code-block:: python

    {
        "architecture": _("Architecture"),
        "kernel_id": _("Kernel ID"),
        "ramdisk_id": _("Ramdisk ID"),
        "image_state": _("Euca2ools state"),
        "project_id": _("Project ID"),
        "image_type": _("Image Type")
    }

Used to customize the titles for image custom property attributes that
appear on image detail pages.

IMAGE_RESERVED_CUSTOM_PROPERTIES
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2014.2(Juno)

Default: ``[]``

A list of image custom property keys that should not be displayed in the
Update Metadata tree.

This setting can be used in the case where a separate panel is used for
managing a custom property or if a certain custom property should never be
edited.

IMAGES_ALLOW_LOCATION
~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 10.0.0(Newton)

Default: ``False``

If set to ``True``, this setting allows users to specify an image location
(URL) as the image source when creating or updating images. Depending on
the Glance version, the ability to set an image location is controlled by
policies and/or the Glance configuration. Therefore IMAGES_ALLOW_LOCATION
should only be set to ``True`` if Glance is configured to allow specifying a
location. This setting has no effect when the Keystone catalog doesn't contain
a Glance v2 endpoint.

IMAGES_LIST_FILTER_TENANTS
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2013.1(Grizzly)

Default: ``None``

A list of dictionaries to add optional categories to the image fixed filters
in the Images panel, based on project ownership.

Each dictionary should contain a `tenant` attribute with the project
id, and optionally a `text` attribute specifying the category name, and
an `icon` attribute that displays an icon in the filter button. The
icon names are based on the default icon theme provided by Bootstrap.

Example:

.. code-block:: python

   [{'text': 'Official',
     'tenant': '27d0058849da47c896d205e2fc25a5e8',
     'icon': 'fa-check'}]

OPENSTACK_IMAGE_BACKEND
~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2013.2(Havana)

Default:

.. code-block:: python

    {
        'image_formats': [
            ('', _('Select format')),
            ('aki', _('AKI - Amazon Kernel Image')),
            ('ami', _('AMI - Amazon Machine Image')),
            ('ari', _('ARI - Amazon Ramdisk Image')),
            ('docker', _('Docker')),
            ('iso', _('ISO - Optical Disk Image')),
            ('qcow2', _('QCOW2 - QEMU Emulator')),
            ('raw', _('Raw')),
            ('vdi', _('VDI')),
            ('vhd', _('VHD')),
            ('vmdk', _('VMDK'))
        ]
    }

Used to customize features related to the image service, such as the list of
supported image formats.

Keystone
--------

ALLOW_USERS_CHANGE_EXPIRED_PASSWORD
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 16.0.0(Train)

Default: ``True``

When enabled, this setting lets users change their password after it has
expired or when it is required to be changed on first use. Disabling it will
force such users to either use the command line interface to change their
password, or contact the system administrator.


AUTHENTICATION_PLUGINS
~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2015.1(Kilo)

Default:

.. code-block:: python

    [
        'openstack_auth.plugin.password.PasswordPlugin',
        'openstack_auth.plugin.token.TokenPlugin'
    ]

A list of authentication plugins to be used. In most cases, there is no need to
configure this.

AUTHENTICATION_URLS
~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2015.1(Kilo)

Default: ``['openstack_auth.urls']``

A list of modules from which to collate authentication URLs from. The default
option adds URLs from the django-openstack-auth module however others will be
required for additional authentication mechanisms.

AVAILABLE_REGIONS
~~~~~~~~~~~~~~~~~

.. versionadded:: 2012.1(Essex)

Default: ``None``

A list of tuples which define multiple regions. The tuple format is
``('http://{{ keystone_host }}:5000/v3', '{{ region_name }}')``. If any regions
are specified the login form will have a dropdown selector for authenticating
to the appropriate region, and there will be a region switcher dropdown in
the site header when logged in.

You should also define `OPENSTACK_KEYSTONE_URL`_ to indicate which of
the regions is the default one.


DEFAULT_SERVICE_REGIONS
~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 12.0.0(Pike)

Default: ``{}``

The default service region is set on a per-endpoint basis, meaning that once
the user logs into some Keystone endpoint, if a default service region is
defined for it in this setting and exists within Keystone catalog, it will be
set as the initial service region in this endpoint. By default it is an empty
dictionary because upstream can neither predict service region names in a
specific deployment, nor tell whether this behavior is desired. The key of the
dictionary is a full url of a Keystone endpoint with version suffix, the value
is a region name.

Example:

.. code-block:: python

    DEFAULT_SERVICE_REGIONS = {
        OPENSTACK_KEYSTONE_URL: 'RegionOne'
    }

As of Rocky you can optionally you can set ``'*'`` as the key, and if no
matching endpoint is found this will be treated as a global default.

Example:

.. code-block:: python

    DEFAULT_SERVICE_REGIONS = {
        '*': 'RegionOne',
        OPENSTACK_KEYSTONE_URL: 'RegionTwo'
    }

ENABLE_CLIENT_TOKEN
~~~~~~~~~~~~~~~~~~~

.. versionadded:: 10.0.0(Newton)

Default: ``True``

This setting will Enable/Disable access to the Keystone Token to the
browser.

ENFORCE_PASSWORD_CHECK
~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2015.1(Kilo)

Default: ``False``

This setting will display an 'Admin Password' field on the Change Password
form to verify that it is indeed the admin logged-in who wants to change
the password.

KEYSTONE_PROVIDER_IDP_ID
~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 11.0.0(Ocata)

Default: ``"localkeystone"``

This ID is only used for comparison with the service provider IDs.
This ID should not match any service provider IDs.

KEYSTONE_PROVIDER_IDP_NAME
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 11.0.0(Ocata)

Default: ``"Local Keystone"``

The Keystone Provider drop down uses Keystone to Keystone federation to switch
between Keystone service providers. This sets the display name for the Identity
Provider (dropdown display name).

OPENSTACK_KEYSTONE_ADMIN_ROLES
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2015.1(Kilo)

Default: ``["admin"]``

The list of roles that have administrator privileges in this OpenStack
installation. This check is very basic and essentially only works with
keystone v3 with the default policy file. The setting assumes there
is a common ``admin`` like role(s) across services. Example uses of this
setting are:

* to rename the ``admin`` role to ``cloud-admin``
* allowing multiple roles to have administrative privileges, like
  ``["admin", "cloud-admin", "net-op"]``

OPENSTACK_KEYSTONE_BACKEND
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2012.1(Essex)

Default:

.. code-block:: python

    {
        'name': 'native',
        'can_edit_user': True,
        'can_edit_group': True,
        'can_edit_project': True,
        'can_edit_domain': True,
        'can_edit_role': True,
    }

A dictionary containing settings which can be used to identify the
capabilities of the auth backend for Keystone.

If Keystone has been configured to use LDAP as the auth backend then set
``can_edit_user`` and ``can_edit_project`` to ``False`` and name to ``"ldap"``.

OPENSTACK_KEYSTONE_DEFAULT_DOMAIN
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2013.2(Havana)

Default: ``"Default"``

Overrides the default domain used when running on single-domain model
with Keystone V3. All entities will be created in the default domain.

OPENSTACK_KEYSTONE_DEFAULT_ROLE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2011.3(Diablo)

Default: ``"_member_"``

The name of the role which will be assigned to a user when added to a project.
This value must correspond to an existing role name in Keystone. In general,
the value should match the ``member_role_name`` defined in ``keystone.conf``.

OPENSTACK_KEYSTONE_DOMAIN_CHOICES
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 12.0.0(Pike)

Default:

.. code-block:: python

    (
        ('Default', 'Default'),
    )

If `OPENSTACK_KEYSTONE_DOMAIN_DROPDOWN`_ is enabled, this option can be used to
set the available domains to choose from. This is a list of pairs whose first
value is the domain name and the second is the display name.

OPENSTACK_KEYSTONE_DOMAIN_DROPDOWN
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 12.0.0(Pike)

Default: ``False``

Set this to True if you want available domains displayed as a dropdown menu on
the login screen. It is strongly advised NOT to enable this for public clouds,
as advertising enabled domains to unauthenticated customers irresponsibly
exposes private information. This should only be used for private clouds where
the dashboard sits behind a corporate firewall.

OPENSTACK_KEYSTONE_FEDERATION_MANAGEMENT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 9.0.0(Mitaka)

Default: ``False``

Set this to True to enable panels that provide the ability for users to manage
Identity Providers (IdPs) and establish a set of rules to map federation
protocol attributes to Identity API attributes. This extension requires v3.0+
of the Identity API.

OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2013.2(Havana)

Default: ``False``

Set this to True if running on multi-domain model. When this is enabled, it
will require user to enter the Domain name in addition to username for login.

OPENSTACK_KEYSTONE_URL
~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2011.3(Diablo)

.. seealso::

  Horizon's `OPENSTACK_HOST`_ documentation

Default: ``"http://%s:5000/v3" % OPENSTACK_HOST``

The full URL for the Keystone endpoint used for authentication. Unless you
are using HTTPS, running your Keystone server on a nonstandard port, or using
a nonstandard URL scheme you shouldn't need to touch this setting.

PASSWORD_EXPIRES_WARNING_THRESHOLD_DAYS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 12.0.0(Pike)

Default: ``-1``

Password will have an expiration date when using keystone v3 and enabling the
feature. This setting allows you to set the number of days that the user will
be alerted prior to the password expiration. Once the password expires keystone
will deny the access and users must contact an admin to change their password.
Setting this value to ``N`` days means the user will be alerted when the
password expires in less than ``N+1`` days. ``-1`` disables the feature.

PROJECT_TABLE_EXTRA_INFO
~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 10.0.0(Newton)

.. seealso::

  `USER_TABLE_EXTRA_INFO`_ for the equivalent setting on the Users table

Default: ``{}``

Adds additional information for projects as extra attributes. Projects can have
extra attributes as defined by Keystone v3. This setting allows those
attributes to be shown in Horizon.

For example:

.. code-block:: python

    PROJECT_TABLE_EXTRA_INFO = {
        'phone_num': _('Phone Number'),
    }

SECURE_PROXY_ADDR_HEADER
~~~~~~~~~~~~~~~~~~~~~~~~

Default: ``False``

If horizon is behind a proxy server and the proxy is configured, the IP address
from request is passed using header variables inside the request. The header
name depends on a proxy or a load-balancer. This setting specifies the name of
the header with remote IP address. The main use is for authentication log
(success or fail) displaing the IP address of the user.
The commom value for this setting is ``HTTP_X_REAL_IP`` or
``HTTP_X_FORWARDED_FOR``.
If not present, then ``REMOTE_ADDR`` header is used. (``REMOTE_ADDR`` is the
field of Django HttpRequest object which contains IP address of the client.)

TOKEN_DELETION_DISABLED
~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 10.0.0(Newton)

Default: ``False``

This setting allows deployers to control whether a token is deleted on log out.
This can be helpful when there are often long running processes being run
in the Horizon environment.

TOKEN_TIMEOUT_MARGIN
~~~~~~~~~~~~~~~~~~~~

Default: ``0``

A time margin in seconds to subtract from the real token's validity. An example
use case is that the token can be valid once the middleware passed, and
invalid (timed-out) during a view rendering and this generates authorization
errors during the view rendering. By setting this value to a few seconds, you
can avoid token expiration during a view rendering.

USER_TABLE_EXTRA_INFO
~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 10.0.0(Newton)

.. seealso::

  `PROJECT_TABLE_EXTRA_INFO`_ for the equivalent setting on the Projects table

Default: ``{}``

Adds additional information for users as extra attributes. Users can have
extra attributes as defined by Keystone v3. This setting allows those
attributes to be shown in Horizon.

For example:

.. code-block:: python

    USER_TABLE_EXTRA_INFO = {
        'phone_num': _('Phone Number'),
    }

WEBSSO_CHOICES
~~~~~~~~~~~~~~

.. versionadded:: 2015.1(Kilo)

Default:

.. code-block:: python

    (
        ("credentials", _("Keystone Credentials")),
        ("oidc", _("OpenID Connect")),
        ("saml2", _("Security Assertion Markup Language"))
    )

This is the list of authentication mechanisms available to the user. It
includes Keystone federation protocols such as OpenID Connect and SAML, and
also keys that map to specific identity provider and federation protocol
combinations (as defined in `WEBSSO_IDP_MAPPING`_). The list of choices is
completely configurable, so as long as the id remains intact. Do not remove
the credentials mechanism unless you are sure. Once removed, even admins will
have no way to log into the system via the dashboard.

WEBSSO_ENABLED
~~~~~~~~~~~~~~

.. versionadded:: 2015.1(Kilo)

Default: ``False``

Enables keystone web single-sign-on if set to True. For this feature to work,
make sure that you are using Keystone V3 and Django OpenStack Auth V1.2.0 or
later.

WEBSSO_IDP_MAPPING
~~~~~~~~~~~~~~~~~~

.. versionadded:: 8.0.0(Liberty)

Default: ``{}``

A dictionary of specific identity provider and federation protocol combinations.
From the selected authentication mechanism, the value will be looked up as keys
in the dictionary. If a match is found, it will redirect the user to a identity
provider and federation protocol specific WebSSO endpoint in keystone,
otherwise it will use the value as the protocol_id when redirecting to the
WebSSO by protocol endpoint.

Example:

.. code-block:: python

    WEBSSO_CHOICES =  (
        ("credentials", _("Keystone Credentials")),
        ("oidc", _("OpenID Connect")),
        ("saml2", _("Security Assertion Markup Language")),
        ("acme_oidc", "ACME - OpenID Connect"),
        ("acme_saml2", "ACME - SAML2")
    )

    WEBSSO_IDP_MAPPING = {
        "acme_oidc": ("acme", "oidc"),
        "acme_saml2": ("acme", "saml2")
    }

.. note::

    The value is expected to be a tuple formatted as: (<idp_id>, <protocol_id>)

WEBSSO_INITIAL_CHOICE
~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2015.1(Kilo)

Default: ``"credentials"``

Specifies the default authentication mechanism. When user lands on the login
page, this is the first choice they will see.

WEBSSO_DEFAULT_REDIRECT
~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 15.0.0(Stein)

Default: ``False``

Allows to redirect on login to the IdP provider defined on PROTOCOL and REGION
In cases you have a single IdP providing websso, in order to improve user
experience, you can redirect on the login page to the IdP directly by
specifying WEBSSO_DEFAULT_REDIRECT_PROTOCOL and WEBSSO_DEFAULT_REDIRECT_REGION
variables.

WEBSSO_DEFAULT_REDIRECT_PROTOCOL
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 15.0.0(Stein)

Default: ``None``

Allows to specify the protocol for the IdP to contact if the
WEBSSO_DEFAULT_REDIRECT is set to True

WEBSSO_DEFAULT_REDIRECT_REGION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 15.0.0(Stein)

Default: ``OPENSTACK_KEYSTONE_URL``

Allows to specify thee region of the IdP to contact if the
WEBSSO_DEFAULT_REDIRECT is set to True

WEBSSO_DEFAULT_REDIRECT_LOGOUT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 15.0.0(Stein)

Default: ``None``

Allows to specify a callback to the IdP to cleanup the SSO resources.
Once the user logs out it will redirect to the IdP log out method.

WEBSSO_KEYSTONE_URL
~~~~~~~~~~~~~~~~~~~

.. versionadded:: 15.0.0(Stein)

Default: None

The full auth URL for the Keystone endpoint used for web single-sign-on
authentication. Use this when ``OPENSTACK_KEYSTONE_URL`` is set to an internal
Keystone endpoint and is not reachable from the external network where the
identity provider lives. This URL will take precedence over
``OPENSTACK_KEYSTONE_URL`` if the login choice is an external
identity provider (IdP).

Neutron
-------

ALLOWED_PRIVATE_SUBNET_CIDR
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 10.0.0(Newton)

Default:

.. code-block:: python

    {
        'ipv4': [],
        'ipv6': []
    }

A dictionary used to restrict user private subnet CIDR range.
An empty list means that user input will not be restricted
for a corresponding IP version. By default, there is
no restriction for both IPv4 and IPv6.

Example:

.. code-block:: python

    {
        'ipv4': [
            '192.168.0.0/16',
            '10.0.0.0/8'
        ],
        'ipv6': [
            'fc00::/7',
        ]
    }


OPENSTACK_NEUTRON_NETWORK
~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2013.1(Grizzly)

Default:

.. code-block:: python

    {
        'default_dns_nameservers': [],
        'enable_auto_allocated_network': False,
        'enable_distributed_router': False,
        'enable_fip_topology_check': True,
        'enable_ha_router': False,
        'enable_ipv6': True,
        'enable_quotas': False,
        'enable_rbac_policy': True,
        'enable_router': True,
        'extra_provider_types': {},
        'physical_networks': [],
        'segmentation_id_range': {},
        'supported_provider_types': ["*"],
        'supported_vnic_types': ["*"],
    }

A dictionary of settings which can be used to enable optional services provided
by Neutron and configure Neutron specific features.  The following options are
available.

default_dns_nameservers
#######################

.. versionadded:: 10.0.0(Newton)

Default: ``None`` (Empty)

Default DNS servers you would like to use when a subnet is created. This is
only a default. Users can still choose a different list of dns servers.

Example: ``["8.8.8.8", "8.8.4.4", "208.67.222.222"]``

enable_auto_allocated_network
#############################

.. versionadded:: 14.0.0(Rocky)

Default: ``False``

Enable or disable Nova and Neutron 'get-me-a-network' feature.
This sets up a neutron network topology for a project if there is no network
in the project. It simplifies the workflow when launching a server.
Horizon checks if both nova and neutron support the feature and enable it
only when supported. However, whether the feature works properly depends on
deployments, so this setting is disabled by default.
(The detail on the required preparation is described in `the Networking Guide
<https://docs.openstack.org/neutron/latest/admin/config-auto-allocation.html>`__.)

enable_distributed_router
#########################

.. versionadded:: 2014.2(Juno)

Default: ``False``

Enable or disable Neutron distributed virtual router (DVR) feature in
the Router panel. For the DVR feature to be enabled, this option needs
to be set to True and your Neutron deployment must support DVR. Even
when your Neutron plugin (like ML2 plugin) supports DVR feature, DVR
feature depends on l3-agent configuration, so deployers should set this
option appropriately depending on your deployment.

enable_fip_topology_check
#########################

.. versionadded:: 8.0.0(Liberty)

Default: ``True``

The Default Neutron implementation needs a router with a gateway to associate a
FIP. So by default a topology check will be performed by horizon to list only
VM ports attached to a network which is itself attached to a router with an
external gateway. This is to prevent from setting a FIP to a port which will
fail with an error.
Some Neutron vendors do not require it. Some can even attach a FIP to any port
(e.g.: OpenContrail) owned by a tenant.
Set to False if you want to be able to associate a FIP to an instance on a
subnet with no router if your Neutron backend allows it.

enable_ha_router
################

.. versionadded:: 2014.2(Juno)

Default: ``False``

Enable or disable HA (High Availability) mode in Neutron virtual router
in the Router panel. For the HA router mode to be enabled, this option needs
to be set to True and your Neutron deployment must support HA router mode.
Even when your Neutron plugin (like ML2 plugin) supports HA router mode,
the feature depends on l3-agent configuration, so deployers should set this
option appropriately depending on your deployment.

enable_ipv6
###########

.. versionadded:: 2014.2(Juno)

Default: ``False``

Enable or disable IPv6 support in the Network panels. When disabled, Horizon
will only expose IPv4 configuration for networks.

enable_quotas
#############

Default: ``False``

Enable support for Neutron quotas feature. To make this feature work
appropriately, you need to use Neutron plugins with quotas extension support
and quota_driver should be DbQuotaDriver (default config).

enable_rbac_policy
##################

.. versionadded:: 15.0.0(Stein)

Default: ``True``

Set this to True to enable RBAC Policies panel that provide the ability for
users to use RBAC function. This option only affects when Neutron is enabled.

enable_router
#############

.. versionadded:: 2014.2(Juno)

Default: ``True``

Enable (``True``) or disable (``False``) the panels and menus related to router
and Floating IP features. This option only affects when Neutron is enabled. If
your Neutron deployment has no support for Layer-3 features, or you do not wish
to provide the Layer-3 features through the Dashboard, this should be set to
``False``.

extra_provider_types
####################

.. versionadded:: 10.0.0(Newton)

Default: ``{}``

For use with the provider network extension.
This is a dictionary to define extra provider network definitions.
Network types supported by Neutron depend on the configured plugin.
Horizon has predefined provider network types but horizon cannot cover
all of them. If you are using a provider network type not defined
in advance, you can add a definition through this setting.

The **key** name of each item in this must be a network type used
in the Neutron API. **value** should be a dictionary which contains
the following items:

* ``display_name``: string displayed in the network creation form.
* ``require_physical_network``: a boolean parameter which indicates
  this network type requires a physical network.
* ``require_segmentation_id``: a boolean parameter which indicates
  this network type requires a segmentation ID.
  If True, a valid segmentation ID range must be configured
  in ``segmentation_id_range`` settings above.

Example:

.. code-block:: python

    {
        'awesome': {
            'display_name': 'Awesome',
            'require_physical_network': False,
            'require_segmentation_id': True,
        },
    }

physical_networks
#################

.. versionadded:: 12.0.0(Pike)

Default: ``[]``

Default to an empty list and the physical network field on the admin create
network modal will be a regular input field where users can type in the name
of the physical network to be used.
If it is set to a list of available physical networks, the physical network
field will be shown as a dropdown menu where users can select a physical
network to be used.

Example: ``['default', 'test']``

segmentation_id_range
#####################

.. versionadded:: 2014.2(Juno)

Default: ``{}``

For use with the provider network extension. This is a dictionary where each
key is a provider network type and each value is a list containing two numbers.
The first number is the minimum segmentation ID that is valid. The second
number is the maximum segmentation ID. Pertains only to the vlan, gre, and
vxlan network types. By default this option is not provided and each minimum
and maximum value will be the default for the provider network type.

Example:

.. code-block:: python

    {
        'vlan': [1024, 2048],
        'gre': [4094, 65536]
    }

supported_provider_types
########################

.. versionadded:: 2014.2(Juno)

Default: ``["*"]``

For use with the provider network extension. Use this to explicitly set which
provider network types are supported. Only the network types in this list will
be available to choose from when creating a network.
Network types defined in Horizon or defined in `extra_provider_types`_
settings can be specified in this list.
As of the Newton release, the network types defined in Horizon include
network types supported by Neutron ML2 plugin with Open vSwitch driver
(``local``, ``flat``, ``vlan``, ``gre``, ``vxlan`` and ``geneve``)
and supported by Midonet plugin (``midonet`` and ``uplink``).
``["*"]`` means that all provider network types supported by Neutron
ML2 plugin will be available to choose from.

Example: ``['local', 'flat', 'gre']``

supported_vnic_types
####################

.. versionadded:: 2015.1(Kilo)

.. versionchanged:: 12.0.0(Pike)

    Added ``virtio-forwarder`` VNIC type
    Clarified VNIC type availability for users and operators


Default ``['*']``

For use with the port binding extension. Use this to explicitly set which VNIC
types are available for users to choose from, when creating or editing a port.
The VNIC types actually supported are determined by resource availability and
Neutron ML2 plugin support.
Currently, error reporting for users selecting an incompatible or unavailable
VNIC type is restricted to receiving a message from the scheduler that the
instance cannot spawn because of insufficient resources.
VNIC types include ``normal``, ``direct``, ``direct-physical``, ``macvtap``,
``baremetal`` and ``virtio-forwarder``. By default all VNIC types will be
available to choose from.

Example: ``['normal', 'direct']``

To disable VNIC type selection, set an empty list (``[]``) or ``None``.

Nova
----

CREATE_INSTANCE_FLAVOR_SORT
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2013.2(Havana)

Default:

.. code-block:: python

    {
        'key': 'ram'
    }

When launching a new instance the default flavor is sorted by RAM usage in
ascending order.
You can customize the sort order by: id, name, ram, disk and vcpus.
Additionally, you can insert any custom callback function. You can also
provide a flag for reverse sort.
See the description in local_settings.py.example for more information.

This example sorts flavors by vcpus in descending order:

.. code-block:: python

    CREATE_INSTANCE_FLAVOR_SORT = {
         'key':'vcpus',
         'reverse': True,
    }

CONSOLE_TYPE
~~~~~~~~~~~~

.. versionadded:: 2013.2(Havana)

.. versionchanged:: 2014.2(Juno)

    Added the ``None`` option, which deactivates the in-browser console

.. versionchanged:: 2015.1(Kilo)

    Added the ``SERIAL`` option

.. versionchanged:: 2017.11(Queens)

    Added the ``MKS`` option

Default:  ``"AUTO"``

This setting specifies the type of in-browser console used to access the VMs.
Valid values are  ``"AUTO"``, ``"VNC"``, ``"SPICE"``, ``"RDP"``,
``"SERIAL"``, ``"MKS"``, and ``None``.

INSTANCE_LOG_LENGTH
~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2015.1(Kilo)

Default:  ``35``

This setting enables you to change the default number of lines displayed for
the log of an instance.
Valid value must be a positive integer.

LAUNCH_INSTANCE_DEFAULTS
~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 9.0.0(Mitaka)

.. versionchanged:: 10.0.0(Newton)

    Added the ``disable_image``, ``disable_instance_snapshot``,
    ``disable_volume`` and ``disable_volume_snapshot`` options.

.. versionchanged:: 12.0.0(Pike)

    Added the ``create_volume`` option.

.. versionchanged:: 15.0.0(Stein)

    Added the ``hide_create_volume`` option.

Default:

.. code-block:: python

    {
        "config_drive": False,
        "create_volume": True,
        "hide_create_volume": False,
        "disable_image": False,
        "disable_instance_snapshot": False,
        "disable_volume": False,
        "disable_volume_snapshot": False,
        "enable_scheduler_hints": True,
    }

A dictionary of settings which can be used to provide the default values for
properties found in the Launch Instance modal. An explanation of each setting
is provided below.

config_drive
############

.. versionadded:: 9.0.0(Mitaka)

Default: ``False``

This setting specifies the default value for the Configuration Drive property.

create_volume
#############

.. versionadded:: 12.0.0(Pike)

Default: ``True``

This setting allows you to specify the default value for the option of creating
a new volume in the workflow for image and instance snapshot sources.

hide_create_volume
##################

.. versionadded:: 15.0.0(Stein)

Default: ``False``

This setting allow your to hide the "Create New Volume" option and rely on the
default value you select with ``create_volume`` to be the most suitable for your
users.

disable_image
#############

.. versionadded:: 10.0.0(Newton)

Default: ``False``

This setting disables Images as a valid boot source for launching instances.
Image sources won't show up in the Launch Instance modal.

disable_instance_snapshot
#########################

.. versionadded:: 10.0.0(Newton)

Default: ``False``

This setting disables Snapshots as a valid boot source for launching instances.
Snapshots sources won't show up in the Launch Instance modal.

disable_volume
##############

.. versionadded:: 10.0.0(Newton)

Default: ``False``

This setting disables Volumes as a valid boot source for launching instances.
Volumes sources won't show up in the Launch Instance modal.

disable_volume_snapshot
#######################

.. versionadded:: 10.0.0(Newton)

Default: ``False``

This setting disables Volume Snapshots as a valid boot source for launching
instances. Volume Snapshots sources won't show up in the Launch Instance modal.

enable_scheduler_hints
######################

.. versionadded:: 9.0.0(Mitaka)

Default: ``True``

This setting specifies whether or not Scheduler Hints can be provided when
launching an instance.

LAUNCH_INSTANCE_LEGACY_ENABLED
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 8.0.0(Liberty)

.. versionchanged:: 9.0.0(Mitaka)

    The default value for this setting has been changed to ``False``

Default: ``False``

This setting enables the Python Launch Instance workflow.

.. note::

    It is possible to run both the AngularJS and Python workflows simultaneously,
    so the other may be need to be toggled with `LAUNCH_INSTANCE_NG_ENABLED`_

LAUNCH_INSTANCE_NG_ENABLED
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 8.0.0(Liberty)

.. versionchanged:: 9.0.0(Mitaka)

    The default value for this setting has been changed to ``True``

Default: ``True``

This setting enables the AngularJS Launch Instance workflow.

.. note::

    It is possible to run both the AngularJS and Python workflows simultaneously,
    so the other may be need to be toggled with `LAUNCH_INSTANCE_LEGACY_ENABLED`_

OPENSTACK_ENABLE_PASSWORD_RETRIEVE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2014.1(Icehouse)

Default: ``"False"``

When set, enables the instance action "Retrieve password" allowing password
retrieval from metadata service.

OPENSTACK_HYPERVISOR_FEATURES
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2012.2(Folsom)

.. versionchanged:: 2014.1(Icehouse)

    ``can_set_mount_point`` and ``can_set_password`` now default to ``False``

Default:

.. code-block:: python

    {
        'can_set_mount_point': False,
        'can_set_password': False,
        'requires_keypair': False,
        'enable_quotas': True
    }

A dictionary containing settings which can be used to identify the
capabilities of the hypervisor for Nova.

The Xen Hypervisor has the ability to set the mount point for volumes attached
to instances (other Hypervisors currently do not). Setting
``can_set_mount_point`` to ``True`` will add the option to set the mount point
from the UI.

Setting ``can_set_password`` to ``True`` will enable the option to set
an administrator password when launching or rebuilding an instance.

Setting ``requires_keypair`` to ``True`` will require users to select
a key pair when launching an instance.

Setting ``enable_quotas`` to ``False`` will make Horizon treat all Nova
quotas as disabled, thus it won't try to modify them. By default, quotas are
enabled.

OPENSTACK_INSTANCE_RETRIEVE_IP_ADDRESSES
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 13.0.0(Queens)

Default: ``True``

This settings controls whether IP addresses of servers are retrieved from
neutron in the project instance table. Setting this to ``False`` may mitigate
a performance issue in the project instance table in large deployments.

If your deployment has no support of floating IP like provider network
scenario, you can set this to ``False`` in most cases. If your deployment
supports floating IP, read the detail below and understand the under-the-hood
before setting this to ``False``.

Nova has a mechanism to cache network info but it is not fast enough
in some cases. For example, when a user associates a floating IP or
updates an IP address of an server port, it is not reflected to the nova
network info cache immediately. This means an action which a user makes
from the horizon instance table is not reflected into the table content
just after the action. To avoid this, horizon retrieves IP address info
from neutron when retrieving a list of servers from nova.

On the other hand, this operation requires a full list of neutron ports
and can potentially lead to a performance issue in large deployments
(`bug 1722417 <https://bugs.launchpad.net/horizon/+bug/1722417>`__).
This issue can be avoided by skipping querying IP addresses to neutron
and setting this to ``False`` achieves this.
Note that when disabling the query to neutron it takes some time until
associated floating IPs are visible in the project instance table and
users may reload the table to check them.

OPENSTACK_NOVA_EXTENSIONS_BLACKLIST
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 8.0.0(Liberty)

Default: ``[]``

Ignore all listed Nova extensions, and behave as if they were unsupported.
Can be used to selectively disable certain costly extensions for performance
reasons.

Swift
-----

SWIFT_FILE_TRANSFER_CHUNK_SIZE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 2015.1(Kilo)

Default: ``512 * 1024``

This setting specifies the size of the chunk (in bytes) for downloading objects
from Swift. Do not make it very large (higher than several dozens of Megabytes,
exact number depends on your connection speed), otherwise you may encounter
socket timeout. The default value is 524288 bytes (or 512 Kilobytes).

Django Settings
===============

.. note::

    This is not meant to be anywhere near a complete list of settings for
    Django. You should always consult the `upstream documentation
    <https://docs.djangoproject.com/en/dev/topics/settings/>`_, especially
    with regards to deployment considerations and security best-practices.

ADD_INSTALLED_APPS
------------------

.. versionadded:: 2015.1(Kilo)

.. seealso::

    `Django's INSTALLED_APPS documentation
    <https://docs.djangoproject.com/en/dev/ref/settings/#installed_apps>`_

A list of Django applications to be prepended to the ``INSTALLED_APPS``
setting. Allows extending the list of installed applications without having
to override it completely.

ALLOWED_HOSTS
-------------

.. versionadded:: 2013.2(Havana)

.. seealso::

    `Django's ALLOWED_HOSTS documentation
    <https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts>`_

Default: ``['localhost']``

This list should contain names (or IP addresses) of the host
running the dashboard; if it's being accessed via name, the
DNS name (and probably short-name) should be added, if it's accessed via
IP address, that should be added. The setting may contain more than one entry.

.. note::

    ALLOWED_HOSTS is required. If Horizon is running in production (DEBUG is
    False), set this with the list of host/domain names that the application
    can serve. For more information see `Django's Allowed Hosts documentation
    <https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts>`_

.. _debug_setting:

DEBUG
-----

.. versionadded:: 2011.2(Cactus)

.. seealso::

    `Django's DEBUG documentation
    <https://docs.djangoproject.com/en/dev/ref/settings/#debug>`_

Default: ``True``

Controls whether unhandled exceptions should generate a generic 500 response
or present the user with a pretty-formatted debug information page.

When set, `CACHED_TEMPLATE_LOADERS`_ will not be cached.

This setting should **always** be set to ``False`` for production deployments
as the debug page can display sensitive information to users and attackers
alike.

SECRET_KEY
----------

.. versionadded:: 2012.1(Essex)

.. seealso::

    `Django's SECRET_KEY documentation
    <https://docs.djangoproject.com/en/dev/ref/settings/#secret-key>`_

This should absolutely be set to a unique (and secret) value for your
deployment. Unless you are running a load-balancer with multiple Horizon
installations behind it, each Horizon instance should have a unique secret key.

.. note::

    Setting a custom secret key:

    You can either set it to a specific value or you can let Horizon generate a
    default secret key that is unique on this machine, regardless of the
    amount of Python WSGI workers (if used behind Apache+mod_wsgi). However,
    there may be situations where you would want to set this explicitly, e.g.
    when multiple dashboard instances are distributed on different machines
    (usually behind a load-balancer). Either you have to make sure that a
    session gets all requests routed to the same dashboard instance or you set
    the same SECRET_KEY for all of them.

.. code-block:: python

    from horizon.utils import secret_key

    SECRET_KEY = secret_key.generate_or_read_from_file(
    os.path.join(LOCAL_PATH, '.secret_key_store'))

The ``local_settings.py.example`` file includes a quick-and-easy way to
generate a secret key for a single installation.

STATIC_ROOT
-----------

.. versionadded:: 8.0.0(Liberty)

.. seealso::

    `Django's STATIC_ROOT documentation
    <https://docs.djangoproject.com/en/dev/ref/settings/#static-root>`_

Default: ``<path_to_horizon>/static``

The absolute path to the directory where static files are collected when
collectstatic is run.

STATIC_URL
----------

.. versionadded:: 8.0.0(Liberty)

.. seealso::

    `Django's STATIC_URL documentation
    <https://docs.djangoproject.com/en/dev/ref/settings/#static-url>`_

Default: ``/static/``

URL that refers to files in `STATIC_ROOT`_.

By default this value is ``WEBROOT/static/``.

This value can be changed from the default. When changed, the alias in your
webserver configuration should be updated to match.

.. note::

    The value for STATIC_URL must end in '/'.

This value is also available in the scss namespace with the variable name
$static_url.  Make sure you run ``python manage.py collectstatic`` and
``python manage.py compress`` after any changes to this value in settings.py.

TEMPLATES
---------

.. versionadded:: 10.0.0(Newton)

.. seealso::

    `Django's TEMPLATES documentation
    <https://docs.djangoproject.com/en/dev/ref/settings/#templates>`_

Horizon's usage of the ``TEMPLATES`` involves 3 further settings below;
it is generally advised to use those before attempting to alter the
``TEMPLATES`` setting itself.

ADD_TEMPLATE_DIRS
-----------------

.. versionadded:: 15.0.0(Stein)

Template directories defined here will be added to ``DIRS`` option
of Django ``TEMPLATES`` setting. It is useful when you would like to
load deployment-specific templates.

ADD_TEMPLATE_LOADERS
~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 10.0.0(Newton)

Template loaders defined here will be loaded at the end of `TEMPLATE_LOADERS`_,
after the `CACHED_TEMPLATE_LOADERS`_ and will never have a cached output.

CACHED_TEMPLATE_LOADERS
~~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 10.0.0(Newton)

Template loaders defined here will have their output cached if `DEBUG`_
is set to ``False``.

TEMPLATE_LOADERS
~~~~~~~~~~~~~~~~

.. versionadded:: 10.0.0(Newton)

These template loaders will be the first loaders and get loaded before the
CACHED_TEMPLATE_LOADERS. Use ADD_TEMPLATE_LOADERS if you want to add loaders at
the end and not cache loaded templates.
After the whole settings process has gone through, TEMPLATE_LOADERS will be:

.. code-block:: python

    TEMPLATE_LOADERS += (
        ('django.template.loaders.cached.Loader', CACHED_TEMPLATE_LOADERS),
    ) + tuple(ADD_TEMPLATE_LOADERS)

LOCALE_PATHS
------------

.. versionadded:: 16.0.0(Train)

.. seealso::

    `Django's LOCALE_PATHS documentation
    <https://docs.djangoproject.com/en/2.2/ref/settings/#locale-paths>`_

Default: Absolute paths for `horizon/locale`, `openstack_auth/locale` and
`openstack_dashboard/locale` directories.

Django uses relative paths by default so it causes localization issues
depending on your runtime settings. To avoid this we recommend to use absolute
paths for directories with locales.

Other Settings
==============

KUBECONFIG_ENABLED
------------------

.. versionadded:: TBD

Default: ``False``

Kubernetes clusters can use Keystone as an external identity provider.
Horizon can generate a ``kubeconfig`` file from the application credentials
control panel which can be used for authenticating with a Kubernetes cluster.
This setting enables this behavior.

.. seealso::

   `KUBECONFIG_KUBERNETES_URL`_ and `KUBECONFIG_CERTIFICATE_AUTHORITY_DATA`_
   to provide parameters for the ``kubeconfig`` file.

KUBECONFIG_KUBERNETES_URL
-------------------------

.. versionadded:: TBD

Default: ``""``

A Kubernetes API endpoint URL to be included in the generated ``kubeconfig``
file.

.. seealso::

   `KUBECONFIG_ENABLED`_ to enable the ``kubeconfig`` file generation.

KUBECONFIG_CERTIFICATE_AUTHORITY_DATA
-------------------------------------

.. versionadded:: TBD

Default: ``""``

Kubernetes API endpoint certificate authority data to be included in the
generated ``kubeconfig`` file.

.. seealso::

   `KUBECONFIG_ENABLED`_ to enable the ``kubeconfig`` file generation.
