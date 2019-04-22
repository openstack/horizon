.. _local-conf:

==========
local.conf
==========

Configuring DevStack for Horizon
================================

Place the following content into ``devstack/local.conf`` to start the services
that Horizon supports in DevStack when ``stack.sh`` is run. If you need to use
this with a stable branch you need to add ``stable/<branch name>`` to the end
of each ``enable_plugin`` line (e.g. ``stable/mitaka``). You can also check
out DevStack using a stable branch tag. For more information on DevStack,
see https://docs.openstack.org/devstack/latest/

.. code-block:: ini

    [[local|localrc]]

    ADMIN_PASSWORD=secret
    DATABASE_PASSWORD=$ADMIN_PASSWORD
    RABBIT_PASSWORD=$ADMIN_PASSWORD
    SERVICE_PASSWORD=$ADMIN_PASSWORD

    # Recloning will ensure that your stack is up to date. The downside
    # is overhead on restarts and potentially losing a stable environment.
    # If set to `yes`, will reclone all repos every time stack.sh is run.
    # The default is `no`.
    #
    # RECLONE=yes

    # By default `stack.sh` will only install Python packages if no version is
    # currently installed, or the current version does not match a specified
    # requirement. If `PIP_UPGRADE` is set to `True` then existing required
    # Python packages will be upgraded to the most recent version that matches
    # requirements. This is generally recommended, as most of OpenStack is
    # tested on latest packages, rather than older versions. The default is
    # False.
    #
    # PIP_UPGRADE=TRUE

    # Set `OFFLINE` to `True` to configure `stack.sh` to run cleanly without
    # Internet access. `stack.sh` must have been previously run with Internet
    # access to install prerequisites and fetch repositories.
    #
    # OFFLINE=True

    # Note: there are several network setting changes that may be
    # required to get networking properly configured in your environment.
    # This file is just using the defaults set up by devstack.
    # For a more detailed treatment of devstack network configuration
    # options, please see:
    # https://docs.openstack.org/devstack/latest/guides.html

    # Horizon is enabled by default in Devstack, but since we're developing
    # it's advised to use a separate clone. To disable horizon in DevStack,
    # speeding up stack time, use:
    #
    # disable_service horizon

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
