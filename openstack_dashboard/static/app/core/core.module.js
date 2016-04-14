/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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
   * @name horizon.app.core
   * @description
   *
   * # horizon.app.core
   *
   * This module hosts modules of core functionality and services that supports
   * components added to Horizon via its plugin mechanism.
   */
  angular
    .module('horizon.app.core', [
      'horizon.app.core.cloud-services',
      'horizon.app.core.images',
      'horizon.app.core.metadata',
      'horizon.app.core.openstack-service-api',
      'horizon.app.core.workflow',
      'horizon.framework.conf',
      'horizon.framework.util',
      'horizon.framework.widgets',
      'horizon.dashboard.project.workflow'
    ], config)
    .run([
      'horizon.framework.conf.resource-type-registry.service',
      performRegistrations
    ]);

  config.$inject = ['$provide', '$windowProvider'];

  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'app/core/';
    $provide.constant('horizon.app.core.basePath', path);
  }

  function performRegistrations(registry) {
    // The items in this long list of registrations should ideally placed into
    // respective module declarations.  However, until they are more fully
    // fleshed out there's no reason to pollute the directory/file structure.
    // As a model, the Images registration happens in the images module.
    registry.getResourceType('OS::Glance::Metadef', {
      names: [gettext('Metadata Definition'), gettext('Metadata Definitions')]
    });
    registry.getResourceType('OS::Nova::Server', {
      names: [gettext('Instance'), gettext('Instances')]
    });
    registry.getResourceType('OS::Nova::Flavor', {
      names: [gettext('Flavor'), gettext('Flavors')]
    });
    registry.getResourceType('OS::Nova::Keypair', {
      names: [gettext('Key Pair'), gettext('Key Pairs')]
    });
    registry.getResourceType('OS::Designate::Zone', {
      names: [gettext('DNS Domain'), gettext('DNS Domains')]
    });
    registry.getResourceType('OS::Designate::RecordSet', {
      names: [gettext('DNS Record'), gettext('DNS Records')]
    });
    registry.getResourceType('OS::Cinder::Backup', {
      names: [gettext('Volume Backup'), gettext('Volume Backups')]
    });
    registry.getResourceType('OS::Cinder::Snapshot', {
      names: [gettext('Volume Snapshot'), gettext('Volume Snapshots')]
    });
    registry.getResourceType('OS::Cinder::Volume', {
      names: [gettext('Volume'), gettext('Volumes')]
    });
    registry.getResourceType('OS::Nova::Flavor', {
      names: [gettext('Flavor'), gettext('Flavors')]
    });
    registry.getResourceType('OS::Swift::Account', {
      names: [gettext('Object Account'), gettext('Object Accounts')]
    });
    registry.getResourceType('OS::Swift::Container', {
      names: [gettext('Object Container'), gettext('Object Containers')]
    });
    registry.getResourceType('OS::Swift::Object', {
      names: [gettext('Object'), gettext('Objects')]
    });
    registry.getResourceType('OS::Neutron::HealthMonitor', {
      names: [gettext('Network Health Monitor'), gettext('Network Health Monitors')]
    });
    registry.getResourceType('OS::Neutron::Net', {
      names: [gettext('Network'), gettext('Networks')]
    });
    registry.getResourceType('OS::Neutron::Pool', {
      names: [gettext('Load Balancer Pool'), gettext('Load Balancer Pools')]
    });
    registry.getResourceType('OS::Neutron::PoolMember', {
      names: [gettext('Load Balancer Pool Member'), gettext('Load Balancer Pool Members')]
    });
    registry.getResourceType('OS::Neutron::Port', {
      names: [gettext('Network Port'), gettext('Network Ports')]
    });
    registry.getResourceType('OS::Neutron::Router', {
      names: [gettext('Network Router'), gettext('Network Routers')]
    });
    registry.getResourceType('OS::Neutron::Subnet', {
      names: [gettext('Network Subnet'), gettext('Network Subnets')]
    });
  }

})();
