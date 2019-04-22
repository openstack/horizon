===================
Manual installation
===================

This page covers the basic installation of horizon in a production
environment. If you are looking for a developer environment, see
:ref:`quickstart`.

For the system dependencies, see :doc:`system-requirements`.

Installation
============

.. note::

  In the commands below, substitute "<release>" for your version of choice,
  such as "queens" or "rocky".

  If you use the development version, replace "stable/<release>" with "master".

#. Clone Horizon

   .. code-block:: console

     $ git clone https://opendev.org/openstack/horizon -b stable/<release> --depth=1
     $ cd horizon

#. Install the horizon python module into your system

   .. code-block:: console

     $ sudo pip install -c https://opendev.org/openstack/requirements/raw/branch/stable/<release>/upper-constraints.txt .

Configuration
=============

This section contains a small summary of the critical settings required to run
horizon. For more details, please refer to :ref:`install-settings`.

Settings
--------

Create ``openstack_dashboard/local/local_settings.py``. It is usually a good
idea to copy ``openstack_dashboard/local/local_settings.py.example`` and
edit it. As a minimum, the follow settings will need to be modified:

``DEBUG``
  Set to ``False``
``ALLOWED_HOSTS``
  Set to your domain name(s)
``OPENSTACK_HOST``
  Set to the IP of your Keystone endpoint. You may also
  need to alter ``OPENSTACK_KEYSTONE_URL``

.. note::

  The following steps in the "Configuration" section are optional, but highly
  recommended in production.

Translations
------------

Compile translation message catalogs for internationalization. This step is
not required if you do not need to support languages other than US English.
GNU ``gettext`` tool is required to compile message catalogs.

.. code-block:: console

  $ sudo apt-get install gettext
  $ ./manage.py compilemessages

Static Assets
-------------

Compress your static files by adding ``COMPRESS_OFFLINE = True`` to your
``local_settings.py``, then run the following commands

.. code-block:: console

  $ ./manage.py collectstatic
  $ ./manage.py compress

Logging
-------

Horizons uses Django's logging configuration mechanism, which can be customized
by altering the ``LOGGING`` dictionary in ``local_settings.py``. By default,
Horizon's logging example sets the log level to ``INFO``.

Horizon also uses a number of 3rd-party clients which log separately. The
log level for these can still be controlled through Horizon's ``LOGGING``
config, however behaviors may vary beyond Horizon's control.

For more information regarding configuring logging in Horizon, please
read the `Django logging directive`_ and the `Python logging directive`_
documentation. Horizon is built on Python and Django.

.. _Django logging directive: https://docs.djangoproject.com/en/dev/topics/logging
.. _Python logging directive: https://docs.python.org/2/library/logging.html

Session Storage
---------------

Horizon uses `Django's sessions framework`_ for handling session data. There
are numerous session backends available, which are selected through the
``SESSION_ENGINE`` setting in your ``local_settings.py`` file.

.. _Django's sessions framework: https://docs.djangoproject.com/en/dev/topics/http/sessions/

Memcached
~~~~~~~~~

.. code-block:: python

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

Requirements:

* Memcached service running and accessible
* Python memcached module installed

Database
~~~~~~~~

.. code-block:: python

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
~~~~~~~~~~~~~~~

To mitigate the performance issues of database queries, you can also consider
using Django's ``cached_db`` session backend which utilizes both your database
and caching infrastructure to perform write-through caching and efficient
retrieval. You can enable this hybrid setting by configuring both your database
and cache as discussed above and then using

.. code-block:: python

  SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

Deployment
==========

#. Set up a web server with WSGI support. For example, install Apache web
   server on Ubuntu

   .. code-block:: console

     $ sudo apt-get install apache2 libapache2-mod-wsgi

   You can either use the provided ``openstack_dashboard/wsgi.py`` or
   generate a ``openstack_dashboard/horizon_wsgi.py`` file with the following
   command (which detects if you use a virtual environment or not to
   automatically build an adapted WSGI file)

   .. code-block:: console

     $ ./manage.py make_web_conf --wsgi

   Then configure the web server to host OpenStack dashboard via WSGI.
   For apache2 web server, you may need to create
   ``/etc/apache2/sites-available/horizon.conf``.
   The template in DevStack is a good example of the file.
   https://opendev.org/openstack/devstack/src/branch/master/files/apache-horizon.template
   Or you can automatically generate an apache configuration file. If you
   previously generated an ``openstack_dashboard/horizon_wsgi.py`` file it will
   use that, otherwise will default to using ``openstack_dashboard/wsgi.py``

   .. code-block:: console

     $ ./manage.py make_web_conf --apache > /etc/apache2/sites-available/horizon.conf

   Same as above but if you want SSL support

   .. code-block:: console

     $ ./manage.py make_web_conf --apache --ssl --sslkey=/path/to/ssl/key --sslcert=/path/to/ssl/cert > /etc/apache2/sites-available/horizon.conf

   By default the apache configuration will launch a number of apache processes
   equal to the number of CPUs + 1 of the machine on which you launch the
   ``make_web_conf`` command. If the target machine is not the same or if you
   want to specify the number of processes, add the ``--processes`` option

   .. code-block:: console

     $ ./manage.py make_web_conf --apache --processes 10 > /etc/apache2/sites-available/horizon.conf

#. Enable the above configuration and restart the web server

   .. code-block:: console

     $ sudo a2ensite horizon
     $ sudo service apache2 restart

Next Steps
==========

* :ref:`install-settings` lists the available settings for horizon.
* :ref:`install-customizing` describes how to customize horizon.
