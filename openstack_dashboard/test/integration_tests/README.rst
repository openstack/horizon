Horizon Integration Tests
=========================

Horizon's integration tests treat Horizon as a black box.

Running the integration tests
-----------------------------

#. Set up an OpenStack server

#. Prepare the configuration file at `local-horizon.conf` if you need
   to change the default configurations.
   Note that `horizon.conf` can be used for the same purpose too
   from the historical reason.

   You can generate a sample configuration file by the following command::

      $ oslo-config-generator \
            --namespace openstack_dashboard_integration_tests
            --output-file openstack_dashboard/test/integration_tests/horizon.conf.sample

#. Run the tests. ::

    $ tox -e integration

More information
----------------

https://wiki.openstack.org/wiki/Horizon/Testing/UI

https://wiki.mozilla.org/QA/Execution/Web_Testing/Docs/Automation/StyleGuide#Page_Objects
