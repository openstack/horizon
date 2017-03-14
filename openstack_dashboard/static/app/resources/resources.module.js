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
      .setNames(gettext('Metadata Definition'), gettext('Metadata Definitions'));
    registry.getResourceType('OS::Nova::Server')
      .setNames(gettext('Instance'), gettext('Instances'));
    registry.getResourceType('OS::Nova::Flavor')
      .setNames(gettext('Flavor'), gettext('Flavors'));
    registry.getResourceType('OS::Nova::Hypervisor')
      .setNames(gettext('Hypervisor'), gettext('Hypervisors'));
    registry.getResourceType('OS::Nova::Keypair')
      .setNames(gettext('Key Pair'), gettext('Key Pairs'));
    registry.getResourceType('OS::Designate::Zone')
      .setNames(gettext('DNS Domain'), gettext('DNS Domains'));
    registry.getResourceType('OS::Designate::RecordSet')
      .setNames(gettext('DNS Record'), gettext('DNS Records'));
    registry.getResourceType('OS::Cinder::Backup')
      .setNames(gettext('Volume Backup'), gettext('Volume Backups'));
    registry.getResourceType('OS::Cinder::Snapshot')
      .setNames(gettext('Volume Snapshot'), gettext('Volume Snapshots'));
    registry.getResourceType('OS::Cinder::Volume')
      .setNames(gettext('Volume'), gettext('Volumes'));
    registry.getResourceType('OS::Neutron::HealthMonitor')
      .setNames(gettext('Network Health Monitor'), gettext('Network Health Monitors'));
    registry.getResourceType('OS::Neutron::Net')
      .setNames(gettext('Network'), gettext('Networks'));
    registry.getResourceType('OS::Neutron::Pool')
      .setNames(gettext('Load Balancer Pool'), gettext('Load Balancer Pools'));
    registry.getResourceType('OS::Neutron::PoolMember')
      .setNames(gettext('Load Balancer Pool Member'), gettext('Load Balancer Pool Members'));
    registry.getResourceType('OS::Neutron::Port')
      .setNames(gettext('Network Port'), gettext('Network Ports'));
    registry.getResourceType('OS::Neutron::Router')
      .setNames(gettext('Network Router'), gettext('Network Routers'));
    registry.getResourceType('OS::Neutron::Subnet')
      .setNames(gettext('Network Subnet'), gettext('Network Subnets'));
    registry.getResourceType('OS::Neutron::FloatingIP')
     .setNames(gettext('Floating IP'), gettext('Floating IPs'));
    registry.getResourceType('OS::Neutron::SecurityGroup')
      .setNames(gettext('Security Group'), gettext('Security Groups'));
    registry.getResourceType('OS::Neutron::Trunk')
      .setNames(gettext('Trunk'), gettext('Trunks'));
    registry.getResourceType('OS::Keystone::User')
      .setNames(gettext('User'), gettext('Users'));
    registry.getResourceType('OS::Keystone::Group')
      .setNames(gettext('Group'), gettext('Groups'));
    registry.getResourceType('OS::Keystone::Project')
      .setNames(gettext('Project'), gettext('Projects'));
    registry.getResourceType('OS::Keystone::Role')
      .setNames(gettext('Role'), gettext('Roles'));
  }
})();
