==========
local.conf
==========

Configuring DevStack for Horizon
================================

Place the following content into `devstack/local.conf` to start the services
that Horizon supports in DevStack when `stack.sh` is run. If you need to use
this with a stable branch you need to add ``stable/<branch name>`` to the end
of each ``enable_plugin`` line (e.g. ``stable/mitaka``). You should also check
out devstack using the same stable branch tag.

::

    [[local|localrc]]

    ADMIN_PASSWORD=secret
    DATABASE_PASSWORD=$ADMIN_PASSWORD
    RABBIT_PASSWORD=$ADMIN_PASSWORD
    SERVICE_PASSWORD=$ADMIN_PASSWORD

    # Recloning will insure that your stack is up to date. The downside
    # is overhead on restarts and potentially losing a stable environment.
    # If set to yes, will reclone all repos every time stack.sh is run.
    # The default is no.
    # RECLONE=yes

    # Set ``OFFLINE`` to ``True`` to configure ``stack.sh`` to run cleanly without
    # Internet access. ``stack.sh`` must have been previously run with Internet
    # access to install prerequisites and fetch repositories.
    # OFFLINE=True

    # Note: there are several network setting changes that may be
    # required to get networking properly configured in your environment.
    # This file is just using the defaults set up by devstack.
    # For a more detailed treatment of devstack network configuration
    # options, please see: http://devstack.org/guides/single-machine.html

    # Horizon is enabled by default in Devstack, but since we're developing
    # it's advised to use a separate clone. To disable horizon in devstack,
    # speeding up stack time, use:
    # disable_service horizon

    ### Supported Services
    # The following panels and plugins are part of the Horizon tree
    # and currently supported by the Horizon maintainers

    # Enable Swift (Object Store) without replication
    enable_service s-proxy s-object s-container s-account
    SWIFT_HASH=66a3d6b56c1f479c8b4e70ab5c2000f5
    SWIFT_REPLICAS=1
    SWIFT_DATA_DIR=$DEST/data/swift

    # Enable Heat
    enable_plugin heat https://git.openstack.org/openstack/heat

    # Enable VPN plugin for neutron
    enable_plugin neutron-vpnaas https://git.openstack.org/openstack/neutron-vpnaas

    # Enable Firewall plugin for neutron
    enable_plugin neutron-fwaas https://git.openstack.org/openstack/neutron-fwaas

    # Enable Ceilometer (Metering)
    enable_service ceilometer-acompute ceilometer-acentral ceilometer-anotification ceilometer-collector ceilometer-api

    ### Plugins
    # Horizon has a large number of plugins, documented at
    # http://docs.openstack.org/developer/horizon/plugin_registry.html
    # See the individual repos for information on installing them.

    [[post-config|$GLANCE_API_CONF]]
    [DEFAULT]
    default_store=file
