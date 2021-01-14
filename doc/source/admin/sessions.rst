========================================
Set up session storage for the Dashboard
========================================

The Dashboard uses `Django sessions
framework <https://docs.djangoproject.com/en/dev/topics/http/sessions/>`__
to handle user session data. However, you can use any available session
back end. You customize the session back end through the
``SESSION_ENGINE`` setting in your ``local_settings.py`` file.

After architecting and implementing the core OpenStack
services and other required services, combined with the Dashboard
service steps below, users and administrators can use
the OpenStack dashboard. Refer to the
:doc:`OpenStack User Documentation </user/index>`
chapter of the OpenStack End User Guide for
further instructions on logging in to the Dashboard.

The following sections describe the pros and cons of each option as it
pertains to deploying the Dashboard.

Local memory cache
~~~~~~~~~~~~~~~~~~

Local memory storage is the quickest and easiest session back end to set
up, as it has no external dependencies whatsoever. It has the following
significant drawbacks:

- No shared storage across processes or workers.
- No persistence after a process terminates.

The local memory back end is enabled as the default for Horizon solely
because it has no dependencies. It is not recommended for production
use, or even for serious development work.

.. code-block:: python

   SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
   CACHES = {
     'default' : {
       'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'
     }
   }

You can use applications such as ``Memcached`` or ``Redis`` for external
caching. These applications offer persistence and shared storage and are
useful for small-scale deployments and development.

Memcached
---------

Memcached is a high-performance and distributed memory object caching
system providing in-memory key-value store for small chunks of arbitrary
data.

Requirements:

- Memcached service running and accessible.
- Python module ``python-memcached`` installed.

.. code-block:: python

   SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
   CACHES = {
     'default': {
       'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
       'LOCATION': 'my_memcached_host:11211',
     }
   }

Redis
-----

Redis is an open source, BSD licensed, advanced key-value store. It is
often referred to as a data structure server.

Requirements:

- Redis service running and accessible.
- Python modules ``redis`` and ``django-redis`` installed.

.. code-block:: python

   SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
   CACHES = {
       "default": {
           "BACKEND": "redis_cache.cache.RedisCache",
           "LOCATION": "127.0.0.1:6379:1",
           "OPTIONS": {
               "CLIENT_CLASS": "redis_cache.client.DefaultClient",
           }
       }
   }

Initialize and configure the database
-------------------------------------

Database-backed sessions are scalable, persistent, and can be made
high-concurrency and highly available.

However, database-backed sessions are one of the slower session storages
and incur a high overhead under heavy usage. Proper configuration of
your database deployment can also be a substantial undertaking and is
far beyond the scope of this documentation.

#. Start the MySQL command-line client.

   .. code-block:: console

      # mysql

#. Enter the MySQL root user's password when prompted.
#. To configure the MySQL database, create the dash database.

   .. code-block:: console

      mysql> CREATE DATABASE dash;

#. Create a MySQL user for the newly created dash database that has full
   control of the database. Replace DASH\_DBPASS with a password for the
   new user.

   .. code-block:: console

      mysql> GRANT ALL PRIVILEGES ON dash.* TO 'dash'@'%' IDENTIFIED BY 'DASH_DBPASS';
      mysql> GRANT ALL PRIVILEGES ON dash.* TO 'dash'@'localhost' IDENTIFIED BY 'DASH_DBPASS';

#. Enter ``quit`` at the ``mysql>`` prompt to exit MySQL.

#. In the ``local_settings.py`` file, change these options:

   .. code-block:: python

      SESSION_ENGINE = 'django.contrib.sessions.backends.db'
      DATABASES = {
          'default': {
              # Database configuration here
              'ENGINE': 'django.db.backends.mysql',
              'NAME': 'dash',
              'USER': 'dash',
              'PASSWORD': 'DASH_DBPASS',
              'HOST': 'localhost',
              'default-character-set': 'utf8'
          }
      }

#. After configuring the ``local_settings.py`` file as shown, you can run the
   :command:`manage.py migrate` command to populate this newly created
   database.

   .. code-block:: console

      # /usr/share/openstack-dashboard/manage.py migrate

#. To avoid a warning when you restart Apache on Ubuntu, create a
   ``blackhole`` directory in the Dashboard directory, as follows.

   .. code-block:: console

      # mkdir -p /var/lib/dash/.blackhole

#. Restart the Apache service.

#. On Ubuntu, restart the ``nova-api`` service to ensure that the API server
   can connect to the Dashboard without error.

   .. code-block:: console

      # service nova-api restart

Cached database
~~~~~~~~~~~~~~~

To mitigate the performance issues of database queries, you can use the
Django ``cached_db`` session back end, which utilizes both your database
and caching infrastructure to perform write-through caching and
efficient retrieval.

Enable this hybrid setting by configuring both your database and cache,
as discussed previously. Then, set the following value:

.. code-block:: python

   SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

Cookies
~~~~~~~

If you use Django 1.4 or later, the ``signed_cookies`` back end avoids
server load and scaling problems.

This back end stores session data in a cookie, which is stored by the
user's browser. The back end uses a cryptographic signing technique to
ensure session data is not tampered with during transport. This is not
the same as encryption; session data is still readable by an attacker.

The pros of this engine are that it requires no additional dependencies
or infrastructure overhead, and it scales indefinitely as long as the
quantity of session data being stored fits into a normal cookie.

The biggest downside is that it places session data into storage on the
user's machine and transports it over the wire. It also limits the
quantity of session data that can be stored.

See the Django `cookie-based
sessions <https://docs.djangoproject.com/en/dev/topics/http/sessions/#using-cookie-based-sessions>`__
documentation.
