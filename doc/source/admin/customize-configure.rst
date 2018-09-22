=====================================
Customize and configure the Dashboard
=====================================

Once you have the Dashboard installed, you can customize the way
it looks and feels to suit the needs of your environment, your
project, or your business.

You can also configure the Dashboard for a secure HTTPS deployment, or
an HTTP deployment. The standard OpenStack installation uses a non-encrypted
HTTP channel, but you can enable SSL support for the Dashboard.

For information on configuring HTTPS or HTTP, see :ref:`configure_dashboard`.

.. This content is out of date as of the Mitaka release, and needs an
.. update to reflect the most recent work on themeing - JR -.

Customize the Dashboard
~~~~~~~~~~~~~~~~~~~~~~~

The OpenStack Dashboard on Ubuntu installs the
``openstack-dashboard-ubuntu-theme`` package by default. If you do not
want to use this theme, remove it and its dependencies:

.. code-block:: console

   # apt-get remove --auto-remove openstack-dashboard-ubuntu-theme

.. note::

   This guide focuses on the ``local_settings.py`` file.

The following Dashboard content can be customized to suit your needs:

* Logo
* Site colors
* HTML title
* Logo link
* Help URL

Logo and site colors
--------------------

#. Create two PNG logo files with transparent backgrounds using
   the following sizes:

   - Login screen: 365 x 50
   - Logged in banner: 216 x 35

#. Upload your new images to
   ``/usr/share/openstack-dashboard/openstack_dashboard/static/dashboard/img/``.

#. Create a CSS style sheet in
   ``/usr/share/openstack-dashboard/openstack_dashboard/static/dashboard/scss/``.

#. Change the colors and image file names as appropriate. Ensure the
   relative directory paths are the same. The following example file
   shows you how to customize your CSS file:

   .. code-block:: css

      /*
      * New theme colors for dashboard that override the defaults:
      *  dark blue: #355796 / rgb(53, 87, 150)
      *  light blue: #BAD3E1 / rgb(186, 211, 225)
      *
      * By Preston Lee <plee@tgen.org>
      */
      h1.brand {
      background: #355796 repeat-x top left;
      border-bottom: 2px solid #BAD3E1;
      }
      h1.brand a {
      background: url(../img/my_cloud_logo_small.png) top left no-repeat;
      }
      #splash .login {
      background: #355796 url(../img/my_cloud_logo_medium.png) no-repeat center 35px;
      }
      #splash .login .modal-header {
      border-top: 1px solid #BAD3E1;
      }
      .btn-primary {
      background-image: none !important;
      background-color: #355796 !important;
      border: none !important;
      box-shadow: none;
      }
      .btn-primary:hover,
      .btn-primary:active {
      border: none;
      box-shadow: none;
      background-color: #BAD3E1 !important;
      text-decoration: none;
      }

#. Open the following HTML template in an editor of your choice:

   .. code-block:: console

      /usr/share/openstack-dashboard/openstack_dashboard/templates/_stylesheets.html

#. Add a line to include your newly created style sheet. For example,
   ``custom.css`` file:

   .. code-block:: html

      <link href='{{ STATIC_URL }}bootstrap/css/bootstrap.min.css' media='screen' rel='stylesheet' />
      <link href='{{ STATIC_URL }}dashboard/css/{% choose_css %}' media='screen' rel='stylesheet' />
      <link href='{{ STATIC_URL }}dashboard/css/custom.css' media='screen' rel='stylesheet' />

#. Restart the Apache service.

#. To view your changes, reload your Dashboard. If necessary, go back
   and modify your CSS file as appropriate.

HTML title
----------

#. Set the HTML title, which appears at the top of the browser window, by
   adding the following line to ``local_settings.py``:

   .. code-block:: python

      SITE_BRANDING = "Example, Inc. Cloud"

#. Restart Apache for this change to take effect.

Logo link
---------

#. The logo also acts as a hyperlink. The default behavior is to redirect
   to ``horizon:user_home``. To change this, add the following attribute to
   ``local_settings.py``:

   .. code-block:: python

      SITE_BRANDING_LINK = "http://example.com"

#. Restart Apache for this change to take effect.

Help URL
--------

#. By default, the help URL points to https://docs.openstack.org. To change
   this, edit the following attribute in ``local_settings.py``:

   .. code-block:: python

      HORIZON_CONFIG["help_url"] = "http://openstack.mycompany.org"

#. Restart Apache for this change to take effect.

.. _configure_dashboard:

Configure the Dashboard
~~~~~~~~~~~~~~~~~~~~~~~

The following section on configuring the Dashboard for a
secure HTTPS deployment, or a HTTP deployment, uses concrete
examples to ensure the procedure is clear. The file path varies
by distribution, however. If needed, you can also configure
the VNC window size in the Dashboard.

Configure the Dashboard for HTTP
--------------------------------

You can configure the Dashboard for a simple HTTP deployment.
The standard installation uses a non-encrypted HTTP channel.

#. Specify the host for your Identity service endpoint in the
   ``local_settings.py`` file with the ``OPENSTACK_HOST`` setting.

   The following example shows this setting:

   .. code-block:: python

      import os

      from django.utils.translation import ugettext_lazy as _

      DEBUG = False
      TEMPLATE_DEBUG = DEBUG
      PROD = True
      USE_SSL = False

      SITE_BRANDING = 'OpenStack Dashboard'

      # Ubuntu-specific: Enables an extra panel in the 'Settings' section
      # that easily generates a Juju environments.yaml for download,
      # preconfigured with endpoints and credentials required for bootstrap
      # and service deployment.
      ENABLE_JUJU_PANEL = True

      # Note: You should change this value
      SECRET_KEY = 'elj1IWiLoWHgryYxFT6j7cM5fGOOxWY0'

      # Specify a regular expression to validate user passwords.
      # HORIZON_CONFIG = {
      #     "password_validator": {
      #         "regex": '.*',
      #         "help_text": _("Your password does not meet the requirements.")
      #     }
      # }

      LOCAL_PATH = os.path.dirname(os.path.abspath(__file__))

      CACHES = {
          'default': {
              'BACKEND' : 'django.core.cache.backends.memcached.MemcachedCache',
              'LOCATION' : '127.0.0.1:11211'
          }
      }

      # Send email to the console by default
      EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
      # Or send them to /dev/null
      #EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

      # Configure these for your outgoing email host
      # EMAIL_HOST = 'smtp.my-company.com'
      # EMAIL_PORT = 25
      # EMAIL_HOST_USER = 'djangomail'
      # EMAIL_HOST_PASSWORD = 'top-secret!'

      # For multiple regions uncomment this configuration, and add (endpoint, title).
      # AVAILABLE_REGIONS = [
      #     ('http://cluster1.example.com:5000/v3', 'cluster1'),
      #     ('http://cluster2.example.com:5000/v3', 'cluster2'),
      # ]

      OPENSTACK_HOST = "127.0.0.1"
      OPENSTACK_KEYSTONE_URL = "http://%s:5000/v3" % OPENSTACK_HOST
      OPENSTACK_KEYSTONE_DEFAULT_ROLE = "Member"

      # The OPENSTACK_KEYSTONE_BACKEND settings can be used to identify the
      # capabilities of the auth backend for Keystone.
      # If Keystone has been configured to use LDAP as the auth backend then set
      # can_edit_user to False and name to 'ldap'.
      #
      # TODO(tres): Remove these once Keystone has an API to identify auth backend.
      OPENSTACK_KEYSTONE_BACKEND = {
          'name': 'native',
          'can_edit_user': True
      }

      # OPENSTACK_ENDPOINT_TYPE specifies the endpoint type to use for the endpoints
      # in the Keystone service catalog. Use this setting when Horizon is running
      # external to the OpenStack environment. The default is 'internalURL'.
      #OPENSTACK_ENDPOINT_TYPE = "publicURL"

      # The number of Swift containers and objects to display on a single page before
      # providing a paging element (a "more" link) to paginate results.
      API_RESULT_LIMIT = 1000

      # If you have external monitoring links, eg:
      # EXTERNAL_MONITORING = [
      #     ['Nagios','http://foo.com'],
      #     ['Ganglia','http://bar.com'],
      # ]

      LOGGING = {
              'version': 1,
              # When set to True this will disable all logging except
              # for loggers specified in this configuration dictionary. Note that
              # if nothing is specified here and disable_existing_loggers is True,
              # django.db.backends will still log unless it is disabled explicitly.
              'disable_existing_loggers': False,
              'handlers': {
                  'null': {
                      'level': 'DEBUG',
                      'class': 'logging.NullHandler',
                      },
                  'console': {
                      # Set the level to "DEBUG" for verbose output logging.
                      'level': 'INFO',
                      'class': 'logging.StreamHandler',
                      },
                  },
              'loggers': {
                  # Logging from django.db.backends is VERY verbose, send to null
                  # by default.
                  'django.db.backends': {
                      'handlers': ['null'],
                      'propagate': False,
                      },
                  'horizon': {
                      'handlers': ['console'],
                      'propagate': False,
                  },
                  'novaclient': {
                      'handlers': ['console'],
                      'propagate': False,
                  },
                  'keystoneclient': {
                      'handlers': ['console'],
                      'propagate': False,
                  }
              }
      }

   The service catalog configuration in the Identity service determines
   whether a service appears in the Dashboard.
   For the full listing, see :ref:`install-settings`.

#. Restart the Apache HTTP Server.

#. Restart ``memcached``.

Configure the Dashboard for HTTPS
---------------------------------

You can configure the Dashboard for a secured HTTPS deployment.
While the standard installation uses a non-encrypted HTTP channel,
you can enable SSL support for the Dashboard.

This example uses the ``http://openstack.example.com`` domain.
Use a domain that fits your current setup.

#. In the ``local_settings.py`` file, update the following options:

   .. code-block:: python

      USE_SSL = True
      CSRF_COOKIE_SECURE = True
      SESSION_COOKIE_SECURE = True
      SESSION_COOKIE_HTTPONLY = True

   To enable HTTPS, the ``USE_SSL = True`` option is required.

   The other options require that HTTPS is enabled;
   these options defend against cross-site scripting.

#. Edit the ``openstack-dashboard.conf`` file as shown in the
   **Example After**:

   **Example Before**

   .. code-block:: none

      WSGIScriptAlias / /usr/share/openstack-dashboard/openstack_dashboard/wsgi.py
      WSGIDaemonProcess horizon user=www-data group=www-data processes=3 threads=10
      Alias /static /usr/share/openstack-dashboard/openstack_dashboard/static/
      <Location />
        <ifVersion >=2.4>
          Require all granted
        </ifVersion>
        <ifVersion <2.4>
          Order allow,deny
          Allow from all
        </ifVersion>
      </Location>

   **Example After**

   .. code-block:: none

      <VirtualHost *:80>
        ServerName openstack.example.com
        <IfModule mod_rewrite.c>
          RewriteEngine On
          RewriteCond %{HTTPS} off
          RewriteRule (.*) https://%{HTTP_HOST}%{REQUEST_URI}
        </IfModule>
        <IfModule !mod_rewrite.c>
          RedirectPermanent / https://openstack.example.com
        </IfModule>
      </VirtualHost>

      <VirtualHost *:443>
        ServerName openstack.example.com

        SSLEngine On
        # Remember to replace certificates and keys with valid paths in your environment
        SSLCertificateFile /etc/apache2/SSL/openstack.example.com.crt
        SSLCACertificateFile /etc/apache2/SSL/openstack.example.com.crt
        SSLCertificateKeyFile /etc/apache2/SSL/openstack.example.com.key
        SetEnvIf User-Agent ".*MSIE.*" nokeepalive ssl-unclean-shutdown

        # HTTP Strict Transport Security (HSTS) enforces that all communications
        # with a server go over SSL. This mitigates the threat from attacks such
        # as SSL-Strip which replaces links on the wire, stripping away https prefixes
        # and potentially allowing an attacker to view confidential information on the
        # wire
        Header add Strict-Transport-Security "max-age=15768000"

        WSGIScriptAlias / /usr/share/openstack-dashboard/openstack_dashboard/wsgi.py
        WSGIDaemonProcess horizon user=www-data group=www-data processes=3 threads=10
        Alias /static /usr/share/openstack-dashboard/openstack_dashboard/static/
        <Location />
          Options None
          AllowOverride None
          # For Apache http server 2.4 and later:
          <ifVersion >=2.4>
            Require all granted
          </ifVersion>
          # For Apache http server 2.2 and earlier:
          <ifVersion <2.4>
            Order allow,deny
            Allow from all
          </ifVersion>
        </Location>
      </VirtualHost>

   In this configuration, the Apache HTTP Server listens on port 443 and
   redirects all non-secure requests to the HTTPS protocol. The secured
   section defines the private key, public key, and certificate to use.

#. Restart the Apache HTTP Server.

#. Restart ``memcached``.

   If you try to access the Dashboard through HTTP, the browser redirects
   you to the HTTPS page.

   .. note::

      Configuring the Dashboard for HTTPS also requires enabling SSL for
      the noVNC proxy service. On the controller node, add the following
      additional options to the ``[DEFAULT]`` section of the
      ``/etc/nova/nova.conf`` file:

      .. code-block:: ini

         [DEFAULT]
         # ...
         ssl_only = true
         cert = /etc/apache2/SSL/openstack.example.com.crt
         key = /etc/apache2/SSL/openstack.example.com.key

      On the compute nodes, ensure the ``nonvncproxy_base_url`` option
      points to a URL with an HTTPS scheme:

      .. code-block:: ini

         [DEFAULT]
         # ...
         novncproxy_base_url = https://controller:6080/vnc_auto.html
