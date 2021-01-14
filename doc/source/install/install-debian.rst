================================
Install and configure for Debian
================================

This section describes how to install and configure the dashboard
on the controller node.

The only core service required by the dashboard is the Identity service.
You can use the dashboard in combination with other services, such as
Image service, Compute, and Networking. You can also use the dashboard
in environments with stand-alone services such as Object Storage.

.. note::

   This section assumes proper installation, configuration, and operation
   of the Identity service using the Apache HTTP server and Memcached
   service.

Install and configure components
--------------------------------

.. include:: note_configuration_vary_by_distribution.txt





1. Install the packages:

   .. code-block:: console

      # apt install openstack-dashboard-apache

   .. end

2. Respond to prompts for web server configuration.

   .. note::

      The automatic configuration process generates a self-signed
      SSL certificate. Consider obtaining an official certificate
      for production environments.

   .. note::

      There are two modes of installation. One using ``/horizon`` as the URL,
      keeping your default vhost and only adding an Alias directive: this is
      the default. The other mode will remove the default Apache vhost and install
      the dashboard on the webroot. It was the only available option
      before the Liberty release. If you prefer to set the Apache configuration
      manually,  install the ``openstack-dashboard`` package instead of
      ``openstack-dashboard-apache``.





3. Edit the
   ``/etc/openstack-dashboard/local_settings.py``
   file and complete the following actions:

   * Configure the dashboard to use OpenStack services on the
     ``controller`` node:

     .. path /etc/openstack-dashboard/local_settings.py
     .. code-block:: python

        OPENSTACK_HOST = "controller"

     .. end

   * In the Dashboard configuration section, allow your hosts to access
     Dashboard:

     .. path /etc/openstack-dashboard/local_settings.py
     .. code-block:: python

        ALLOWED_HOSTS = ['one.example.com', 'two.example.com']

     .. end

     .. note::

        - Do not edit the ``ALLOWED_HOSTS`` parameter under the Ubuntu
          configuration section.
        - ``ALLOWED_HOSTS`` can also be ``['*']`` to accept all hosts. This
          may be useful for development work, but is potentially insecure
          and should not be used in production. See the
          `Django documentation
          <https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts>`_
          for further information.

   * Configure the ``memcached`` session storage service:

     .. path /etc/openstack-dashboard/local_settings.py
     .. code-block:: python

        SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

        CACHES = {
            'default': {
                 'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
                 'LOCATION': 'controller:11211',
            }
        }

     .. end

     .. note::

        Comment out any other session storage configuration.

   * Enable the Identity API version 3:

     .. path /etc/openstack-dashboard/local_settings.py
     .. code-block:: python

        OPENSTACK_KEYSTONE_URL = "http://%s/identity/v3" % OPENSTACK_HOST

     .. end

   * Enable support for domains:

     .. path /etc/openstack-dashboard/local_settings.py
     .. code-block:: python

        OPENSTACK_KEYSTONE_MULTIDOMAIN_SUPPORT = True

     .. end

   * Configure API versions:

     .. path /etc/openstack-dashboard/local_settings.py
     .. code-block:: python

        OPENSTACK_API_VERSIONS = {
            "identity": 3,
            "image": 2,
            "volume": 3,
        }

     .. end

   * Configure ``Default`` as the default domain for users that you create
     via the dashboard:

     .. path /etc/openstack-dashboard/local_settings.py
     .. code-block:: python

        OPENSTACK_KEYSTONE_DEFAULT_DOMAIN = "Default"

     .. end

   * Configure ``user`` as the default role for
     users that you create via the dashboard:

     .. path /etc/openstack-dashboard/local_settings.py
     .. code-block:: python

        OPENSTACK_KEYSTONE_DEFAULT_ROLE = "user"

     .. end

   * If you chose networking option 1, disable support for layer-3
     networking services:

     .. path /etc/openstack-dashboard/local_settings.py
     .. code-block:: python

        OPENSTACK_NEUTRON_NETWORK = {
            ...
            'enable_router': False,
            'enable_quotas': False,
            'enable_ipv6': False,
            'enable_distributed_router': False,
            'enable_ha_router': False,
            'enable_fip_topology_check': False,
        }

     .. end

   * Optionally, configure the time zone:

     .. path /etc/openstack-dashboard/local_settings.py
     .. code-block:: python

        TIME_ZONE = "TIME_ZONE"

     .. end

     Replace ``TIME_ZONE`` with an appropriate time zone identifier.
     For more information, see the `list of time zones
     <https://en.wikipedia.org/wiki/List_of_tz_database_time_zones>`__.


Finalize installation
---------------------


* Reload the web server configuration:

  .. code-block:: console

     # service apache2 reload

  .. end



