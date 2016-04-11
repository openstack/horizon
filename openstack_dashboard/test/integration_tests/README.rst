Horizon Integration Tests
=========================

Horizon's integration tests treat Horizon as a black box.

Running the integration tests
-----------------------------

#. Set up an OpenStack server

#. Update the configuration file at `horizon.conf` or add overrides
   to that file in `local-horizon.conf` which is ignored by git.

#. Run the tests. ::

    $ ./run_tests.sh --integration

More information
----------------

https://wiki.openstack.org/wiki/Horizon/Testing/UI

https://wiki.mozilla.org/QA/Execution/Web_Testing/Docs/Automation/StyleGuide#Page_Objects
