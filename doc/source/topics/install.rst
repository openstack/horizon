==================
Installing Horizon
==================

This page covers the basic installation of Horizon.

.. _system-requirements-label:

System Requirements
===================

* Python 2.7
* Django 1.6 (1.4 and 1.5 are supported too)
* Minimum required set of running OpenStack services are:

  * Nova
  * Keystone
  * Glance
  * Neutron (unless nova-network is used)

* All other services are optional.
  Horizon supports the following services in Juno release.
  If Keystone endpoint for a service is configured,
  Horizon detects it and enables its support automatically.

  * Swift
  * Cinder
  * Heat
  * Ceilometer
  * Trove
  * Sahara

Installation
============

1. Compile translation message catalogs for internationalization.
   This step is not required if you do not need to support languages
   other than English. GNU ``gettext`` tool is required to compile
   message catalogs::

    $ sudo apt-get install gettext
    $ ./run_tests.sh --compilemessages

   This command compiles translation message catalogs within Python
   virtualenv named ``.venv``. After this step, you can remove
   ``.venv`` directory safely.

2. Install Horizon python module into your system. Run the following
   in the top directory::

    $ sudo pip install .

3. Create ``openstack_dashboard/local/local_settings.py``.
   It is usually a good idea to copy
   ``openstack_dashboard/local/local_settings.py.example`` and edit it.
   At least we need to customize the following variables in this file.

   * ``ALLOWED_HOSTS`` (unless ``DEBUG`` is ``True``)
   * ``OPENSTACK_KEYSTONE_URL``

   For more details, please refer to :doc:`deployment` and :doc:`settings`.

4. Optional: Django has a Compressor feature that performs many enhancements
   for the delivery of static files, including standardization and
   minification/uglification. This processing can be run either online or
   offline (pre-processed). Letting the compression process occur at runtime
   will incur processing and memory use when the resources are first requested;
   doing it ahead of time removes those runtime penalties.

   If you want the static files to be processed before server runtime, you'll
   need to configure your local_settings.py to specify
   ``COMPRESS_OFFLINE = True``, then run the following commands::

    $ ./manage.py collectstatic
    $ ./manage.py compress

5. Set up a web server with WSGI support.
   It is optional but recommended in production deployments.
   For example, install Apache web server on Ubuntu::

    $ sudo apt-get install apache2 libapache2-mod-wsgi

   Then configure the web server to host OpenStack Dashboard via WSGI.
   For apache2 web server, you may need to create
   ``/etc/apache2/sites-available/horizon.conf``.
   The template in devstack is a good example of the file.
   http://git.openstack.org/cgit/openstack-dev/devstack/tree/files/apache-horizon.template

6. Finally, enable the above configuration and restart the web server::

    $ sudo a2ensite horizon
    $ sudo service apache2 restart

Next Steps
==========

* :doc:`deployment` covers some common questions, concerns and pitfalls you
  may encounter when deploying Horizon in a production environment.
* :doc:`settings` lists the available settings for Horizon.
* :doc:`customizing` describes how to customizing Horizon as you want.
