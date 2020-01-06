/*
 *    (c) Copyright 2016 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function () {
  'use strict';

  /**
   * @ngdoc overview
   * @name horizon.app.resources
   * @description
   *
   * # horizon.app.resources
   *
   * This module hosts registered resource types.  This module file may
   * contain individual registrations, or may have sub-modules that
   * more fully contain registrations.
   */
  angular
    .module('horizon.app.resources', [])
    .run(performRegistrations);

  performRegistrations.$inject = [
    'horizon.framework.conf.resource-type-registry.service'
  ];

  function performRegistrations(registry) {
    // The items in this long list of registrations should ideally placed into
    // respective module declarations.  However, until they are more fully
    // fleshed out there's no reason to pollute the directory/file structure.
    // As a model, the Images registration happens in the images module.
    registry.getResourceType('OS::Glance::Metadef')
      .setNames('Metadata Definition', 'Metadata Definitions',
                ngettext('Metadata Definition', 'Metadata Definitions', 1));
    registry.getResourceType('OS::Nova::Server')
      .setNames('Instance', 'Instances', ngettext('Instance', 'Instances', 1));
    registry.getResourceType('OS::Nova::Flavor')
      .setNames('Flavor', 'Flavors', ngettext('Flavor', 'Flavors', 1));
    registry.getResourceType('OS::Nova::Hypervisor')
      .setNames('Hypervisor', 'Hypervisors',
                ngettext('Hypervisor', 'Hypervisors', 1));
    registry.getResourceType('OS::Nova::Keypair')
      .setNames('Key Pair', 'Key Pairs', ngettext('Key Pair', 'Key Pairs', 1));
    registry.getResourceType('OS::Designate::Zone')
      .setNames('DNS Domain', 'DNS Domains',
                ngettext('DNS Domain', 'DNS Domains', 1));
    registry.getResourceType('OS::Designate::RecordSet')
      .setNames('DNS Record', 'DNS Records',
                ngettext('DNS Record', 'DNS Records', 1));
    registry.getResourceType('OS::Cinder::Backup')
      .setNames('Volume Backup', 'Volume Backups',
                ngettext('Volume Backup', 'Volume Backups', 1));
    registry.getResourceType('OS::Cinder::Snapshot')
      .setNames('Volume Snapshot', 'Volume Snapshots',
                ngettext('Volume Snapshot', 'Volume Snapshots', 1));
    registry.getResourceType('OS::Cinder::Volume')
      .setNames('Volume', 'Volumes', ngettext('Volume', 'Volumes', 1));
    registry.getResourceType('OS::Neutron::HealthMonitor')
      .setNames('Network Health Monitor', 'Network Health Monitors',
                ngettext('Network Health Monitor', 'Network Health Monitors', 1));
    registry.getResourceType('OS::Neutron::Net')
      .setNames('Network', 'Networks', ngettext('Network', 'Networks', 1));
    registry.getResourceType('OS::Neutron::Pool')
      .setNames('Load Balancer Pool', 'Load Balancer Pools',
                ngettext('Load Balancer Pool', 'Load Balancer Pools', 1));
    registry.getResourceType('OS::Neutron::PoolMember')
      .setNames('Load Balancer Pool Member', 'Load Balancer Pool Members',
                ngettext('Load Balancer Pool Member', 'Load Balancer Pool Members', 1));
    registry.getResourceType('OS::Neutron::Port')
      .setNames('Network Port', 'Network Ports',
                ngettext('Network Port', 'Network Ports', 1));
    registry.getResourceType('OS::Neutron::Router')
      .setNames('Network Router', 'Network Routers',
                ngettext('Network Router', 'Network Routers', 1));
    registry.getResourceType('OS::Neutron::Subnet')
      .setNames('Network Subnet', 'Network Subnets',
                ngettext('Network Subnet', 'Network Subnets', 1));
    registry.getResourceType('OS::Neutron::FloatingIP')
     .setNames('Floating IP', 'Floating IPs',
               ngettext('Floating IP', 'Floating IPs', 1));
    registry.getResourceType('OS::Neutron::SecurityGroup')
      .setNames('Security Group', 'Security Groups',
                ngettext('Security Group', 'Security Groups', 1));
    registry.getResourceType('OS::Neutron::Trunk')
      .setNames('Trunk', 'Trunks', ngettext('Trunk', 'Trunks', 1));
    registry.getResourceType('OS::Keystone::User')
      .setNames('User', 'Users', ngettext('User', 'Users', 1));
    registry.getResourceType('OS::Keystone::Group')
      .setNames('Group', 'Groups', ngettext('Group', 'Groups', 1));
    registry.getResourceType('OS::Keystone::Project')
      .setNames('Project', 'Projects', ngettext('Project', 'Projects', 1));
    registry.getResourceType('OS::Keystone::Role')
      .setNames('Role', 'Roles', ngettext('Role', 'Roles', 1));
  }
})();
