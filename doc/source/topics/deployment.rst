=================
Deploying Horizon
=================

This guide aims to cover some common questions, concerns and pitfalls you
may encounter when deploying Horizon in a production environment.

.. seealso:: :doc:`settings`

.. note::

    The Service Catalog returned by the Identity Service after a user
    has successfully authenticated determines the dashboards and panels
    that will be available within the OpenStack Dashboard. If you are not
    seeing a particular service you expected (e.g. Object Storage/Swift or
    Networking/Neutron) make sure your Service Catalog is configured correctly.

    Prior to the Essex release of Horizon these features were controlled by
    individual settings in the ``local_settings.py`` file. This code has been
    long-since removed and those pre-Essex settings have no impact now.

Configure Your Identity Service Host
====================================

The one thing you *must* do in order to run Horizon is to specify the
host for your OpenStack Identity Service endpoint. To do this, set the value
of the ``OPENSTACK_HOST`` settings in your ``local_settings.py`` file.

Logging
=======

Logging is an important concern for production deployments, and the intricacies
of good logging configuration go far beyond what can be covered here. However
there are a few points worth noting about the logging included with Horizon,
how to customize it, and where other components may take over:

* Horizon's logging uses Django's logging configuration mechanism, which
  can be customized in your ``local_settings.py`` file through the
  ``LOGGING`` dictionary.
* Horizon's default logging example sets the log level to ``"INFO"``, which is
  a reasonable choice for production deployments. For development, however,
  you may want to change the log level to ``"DEBUG"``.
* Horizon also uses a number of 3rd-party clients which log separately. The
  log level for these can still be controlled through Horizon's ``LOGGING``
  config, however behaviors may vary beyond Horizon's control.
* For more information regarding configuring logging in Horizon, please
  read the `Django logging directive`_ and the `Python logging directive`_
  documentation. Horizon is built on Python and Django.

.. _Django logging directive: https://docs.djangoproject.com/en/1.5/topics/logging
.. _Python logging directive: http://docs.python.org/2/library/logging.html

.. warning::

    At this time there is `a known bug in python-keystoneclient`_ where it will
    log the complete request body of any request sent to Keystone through it
    (including logging passwords in plain text) when the log level is set to
    ``"DEBUG"``. If this behavior is not desired, make sure your log level is
    ``"INFO"`` or higher.

.. _a known bug in python-keystoneclient: https://bugs.launchpad.net/keystone/+bug/1004114

File Uploads
============

Horizon allows users to upload files via their web browser to other OpenStack
services such as Glance and Swift. Files uploaded through this mechanism are
first stored on the Horizon server before being forwarded on - files are not
uploaded directly or streamed as Horizon receives them. As Horizon itself does
not impose any restrictions on the size of file uploads, production deployments
will want to consider configuring their server hosting the Horizon application
to enforce such a limit to prevent large uploads exhausting system resources
and disrupting services. Deployments using Apache2 can use the
`LimitRequestBody directive`_ to achieve this.

Uploads to the Glance image store service tend to be particularly large - in
the order of hundreds of megabytes to multiple gigabytes. Deployments are able
to disable local image uploads through Horizon by setting
``HORIZON_IMAGES_ALLOW_UPLOAD`` to ``False`` in your ``local_settings.py``
file.

.. note::
    This will not disable image creation altogether, as this setting does not
    affect images created by specifying an image location (URL) as the image source.


 .. _LimitRequestBody directive: http://httpd.apache.org/docs/2.2/mod/core.html#limitrequestbody

Session Storage
===============

Horizon uses `Django's sessions framework`_ for handling user session data;
however that's not the end of the story. There are numerous session backends
available, which are controlled through the ``SESSION_ENGINE`` setting in
your ``local_settings.py`` file. What follows is a quick discussion of the
pros and cons of each of the common options as they pertain to deploying
Horizon specifically.

.. _Django's sessions framework: https://docs.djangoproject.com/en/dev/topics/http/sessions/

Local Memory Cache
------------------

Enabled by::

    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    CACHES = {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
    }

Local memory storage is the quickest and easiest session backend to set up,
as it has no external dependencies whatsoever. However, it has two significant
drawbacks:

  * No shared storage across processes or workers.
  * No persistence after a process terminates.

The local memory backend is enabled as the default for Horizon solely because
it has no dependencies. It is not recommended for production use, or even for
serious development work. For better options, read on.

Memcached
---------

Enabled by::

    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    CACHES = {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache'
        'LOCATION': 'my_memcached_host:11211',
    }

External caching using an application such as memcached offers persistence
and shared storage, and can be very useful for small-scale deployment and/or
development. However, for distributed and high-availability scenarios
memcached has inherent problems which are beyond the scope of this
documentation.

Memcached is an extremely fast and efficient cache backend for cases where it
fits the deployment need. But it's not appropriate for all scenarios.

Requirements:

  * Memcached service running and accessible.
  * Python memcached module installed.

Database
--------

Enabled by::

    SESSION_ENGINE = 'django.core.cache.backends.db.DatabaseCache'
    DATABASES = {
        'default': {
            # Database configuration here
        }
    }

Database-backed sessions are scalable (using an appropriate database strategy),
persistent, and can be made high-concurrency and highly-available.

The downside to this approach is that database-backed sessions are one of the
slower session storages, and incur a high overhead under heavy usage. Proper
configuration of your database deployment can also be a substantial
undertaking and is far beyond the scope of this documentation.

Cached Database
---------------

To mitigate the performance issues of database queries, you can also consider
using Django's ``cached_db`` session backend which utilizes both your database
and caching infrastructure to perform write-through caching and efficient
retrieval. You can enable this hybrid setting by configuring both your database
and cache as discussed above and then using::

    SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

Cookies
-------

If you're using Django 1.4 or later, a new session backend is available to you
which avoids server load and scaling problems: the ``signed_cookies`` backend!

This backend stores session data in a cookie which is stored by the
user's browser. The backend uses a cryptographic signing technique to ensure
session data is not tampered with during transport (**this is not the same
as encryption, session data is still readable by an attacker**).

The pros of this session engine are that it doesn't require any additional
dependencies or infrastructure overhead, and it scales indefinitely as long
as the quantity of session data being stored fits into a normal cookie.

The biggest downside is that it places session data into storage on the user's
machine and transports it over the wire. It also limits the quantity of
session data which can be stored.

For a thorough discussion of the security implications of this session backend,
please read the `Django documentation on cookie-based sessions`_.

.. _Django documentation on cookie-based sessions: https://docs.djangoproject.com/en/dev/topics/http/sessions/#using-cookie-based-sessions

Secure Site Recommendations
---------------------------

When implementing Horizon for public usage, with the website served through
HTTPS, it is recommended that the following settings are applied.

To help protect the session cookies from `cross-site scripting`_, add the
following to ``local_settings.py``::

    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

Note that the CSRF_COOKIE_SECURE option is only available from Django 1.4. It
does no harm to have the setting in earlier versions, but it does not take effect.

You can also disable `browser autocompletion`_ for the authentication form by
modifying the ``HORIZON_CONFIG`` dictionary in ``local_settings.py`` by adding
the key ``password_autocomplete`` with the value ``off`` as shown here::

    HORIZON_CONFIG = {
    ...
        'password_autocomplete': 'off',
    }

.. _cross-site scripting: https://www.owasp.org/index.php/HttpOnly
.. _browser autocompletion: https://wiki.mozilla.org/The_autocomplete_attribute_and_web_documents_using_XHTML
