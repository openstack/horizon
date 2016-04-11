==========
local.conf
==========

Configuring DevStack for Horizon
================================

Place the following content into `devstack/local.conf` to start the services
that Horizon supports in DevStack when `stack.sh` is run.
::

    [[local|localrc]]

    ADMIN_PASSWORD=secretadmin
    MYSQL_PASSWORD=secretadmin
    RABBIT_PASSWORD=secretadmin
    SERVICE_PASSWORD=secretadmin
    SERVICE_TOKEN=a682f596-76f3-11e3-b3b2-e716f9080d50

    # Recloning will insure that your stack is up to date. The downside
    # is overhead on restarts and potentially losing a stable environment.
    # If set to yes, will reclone all repos every time stack.sh is run.
    # The default is no.
    #RECLONE=yes

    # Set ``OFFLINE`` to ``True`` to configure ``stack.sh`` to run cleanly without
    # Internet access. ``stack.sh`` must have been previously run with Internet
    # access to install prerequisites and fetch repositories.
    # OFFLINE=True

    # Note: there are several network setting changes that may be
    # required to get networking properly configured in your environment.
    # This file is just using the defaults set up by devstack.
    # For a more detailed treatment of devstack network configuration
    # options, please see: http://devstack.org/guides/single-machine.html

    ### SERVICES

    # Enable Swift (Object Store) without replication
    enable_service s-proxy s-object s-container s-account
    SWIFT_HASH=66a3d6b56c1f479c8b4e70ab5c2000f5
    SWIFT_REPLICAS=1
    SWIFT_DATA_DIR=$DEST/data/swift

    # Enable Neutron (Networking)
    # to use nova net rather than neutron, comment out the following group
    disable_service n-net
    enable_plugin neutron https://git.openstack.org/openstack/neutron
    enable_service q-svc
    enable_service q-agt
    enable_service q-dhcp
    enable_service q-l3
    enable_service q-meta
    enable_service q-metering
    enable_service q-qos
    # end group

    # Enable VPN plugin for neutron
    enable_plugin neutron-vpnaas https://git.openstack.org/openstack/neutron-vpnaas

    # Enable Firewall plugin for neutron
    enable_plugin neutron-fwaas https://git.openstack.org/openstack/neutron-fwaas

    # Enable Load Balancer plugin for neutron
    enable_plugin neutron-lbaas https://git.openstack.org/openstack/neutron-lbaas

    # Enable Ceilometer (Metering)
    enable_service ceilometer-acompute ceilometer-acentral ceilometer-anotification ceilometer-collector ceilometer-api

    ### PLUGINS

    # Enable Sahara (Data Processing)
    enable_plugin sahara git://git.openstack.org/openstack/sahara

    # Enable Trove (Database)
    enable_plugin trove git://git.openstack.org/openstack/trove

    [[post-config|$GLANCE_API_CONF]]
    [DEFAULT]
    default_store=file
