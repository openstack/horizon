===============
Profiling Pages
===============

In the Ocata release of Horizon a new "OpenStack Profiler" panel was
introduced. Once it is enabled and all prerequisites are set up, you can see
which API calls Horizon actually makes when rendering a specific page.
To re-render the page while profiling it, you'll need to use the "Profile"
dropdown menu located in the top right corner of the screen. In order to
be able to use "Profile" menu, the following steps need to be completed:

#. Enable the Developer dashboard by copying ``_9001_developer.py`` from
   ``openstack_dashboard/contrib/developer/enabled/`` to
   ``openstack_dashboard/local/enabled/``.
#. Copy
   ``openstack_dashboard/local/local_settings.d/_9030_profiler_settings.py.example``
   to ``openstack_dashboard/local/local_settings.d/_9030_profiler_settings.py``
#. Copy ``openstack_dashboard/contrib/developer/enabled/_9030_profiler.py`` to
   ``openstack_dashboard/local/enabled/_9030_profiler.py``.
#. To support storing profiler data on server-side, MongoDB cluster needs to be
   installed on your Devstack host (default configuration), see
   `Installing MongoDB
   <https://docs.mongodb.com/manual/tutorial/install-mongodb-on-ubuntu/#install-mongodb-community-edition>`__.
   Then, change the ``bindIp`` key in ``/etc/mongod.conf`` to ``0.0.0.0`` and
   invoke ``sudo service mongod restart``.
#. Collect and compress static assets with
   ``python manage.py collectstatic -c`` and ``python manage.py compress``.
#. Restart the web server.
#. The "Profile" drop-down menu should appear in the top-right corner, you are
   ready to profile your pages!
