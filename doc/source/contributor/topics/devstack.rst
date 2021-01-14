.. _local-conf:

====================
DevStack for Horizon
====================

Place the following content into ``devstack/local.conf`` to start the services
that Horizon supports in DevStack when ``stack.sh`` is run. If you need to use
this with a stable branch you need to add ``stable/<branch name>`` to the end
of each ``enable_plugin`` line (e.g. ``stable/mitaka``). You can also check
out DevStack using a stable branch tag. For more information on DevStack,
see https://docs.openstack.org/devstack/latest/

.. code-block:: ini

    [[local|localrc]]

    ADMIN_PASSWORD="secretadmin"
    DATABASE_PASSWORD="secretdatabase"
    RABBIT_PASSWORD="secretrabbit"
    SERVICE_PASSWORD="secretservice"

    # For DevStack configuration options, see:
    # https://docs.openstack.org/devstack/latest/configuration.html

    # Note: there are several network setting changes that may be
    # required to get networking properly configured in your environment.
    # This file is just using the defaults set up by devstack.
    # For a more detailed treatment of devstack network configuration
    # options, please see:
    # https://docs.openstack.org/devstack/latest/guides.html

    ### Supported Services
    # The following panels and plugins are part of the Horizon tree
    # and currently supported by the Horizon maintainers

    # Enable Swift (Object Store) without replication
    enable_service s-proxy s-object s-container s-account
    SWIFT_HASH=66a3d6b56c1f479c8b4e70ab5c2000f5
    SWIFT_REPLICAS=1
    SWIFT_DATA_DIR=$DEST/data/swift

    # Enable Neutron
    enable_plugin neutron https://opendev.org/openstack/neutron

    # Enable the Trunks extension for Neutron
    enable_service q-trunk

    # Enable the QoS extension for Neutron
    enable_service q-qos

    ### Plugins
    # Horizon has a large number of plugins, documented at
    # https://docs.openstack.org/horizon/latest/install/plugin-registry.html
    # See the individual repos for information on installing them.

    [[post-config|$GLANCE_API_CONF]]
    [DEFAULT]
    default_store=file
