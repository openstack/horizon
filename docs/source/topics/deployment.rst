=================
Deploying Horizon
=================

This guide aims to cover some common questions, concerns and pitfalls you
may encounter when deploying Horizon in a production environment.

Logging
=======

Logging is an important concern for prouction deployments, and the intricacies
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

.. warning::

    At this time there is `a known bug in python-keystoneclient`_ where it will
    log the complete request body of any request sent to Keystone through it
    (including logging passwords in plain text) when the log level is set to
    ``"DEBUG"``. If this behavior is not desired, make sure your log level is
    ``"INFO"`` or higher.

.. _a known bug in python-keystoneclient: https://bugs.launchpad.net/keystone/+bug/1004114

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
fits the depooyment need. But it's not appropriate for all scenarios.

Requirements:

  * Memcached service running and accessible.
  * Python memcached module installed.

Database
--------

Enabled by::

    SESSION_ENGINE = 'django.core.cache.backends.db.DatabaseCache'
    DATABASES = {
        'default': {
            # Databe configuration here
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
