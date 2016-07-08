/**
 * (c) Copyright 2016 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function () {
  'use strict';

  /**
   * @ngdoc overview
   * @ngname horizon.app.core.conf
   *
   * @description
   * Provides features that support app configuration.
   */
  angular
    .module('horizon.app.core.conf', ['horizon.framework.conf'])
    .config(permissionsDecorator);

  permissionsDecorator.$inject = [
    '$provide'
  ];

  /**
   * @name permissionsDecorator
   * @param {Object} $provide
   * @description
   * This decorates the horizon.framework.conf.permissions service to
   * support declarative level permissions based on openstack_dashboard requirements.
   * This adds the following declarative permissions:
   *     'services' (OpenStack services that must be enabled in the current region),
   *     'settings' (OpenStack Dashboard settings that must be enabled)
   *     'policies' (policy rules that must be allowed)
   *
   * For example, these may all be used with the registry service and table column registrations.
   * They are passed through to hz-dynamic-table which asks the permissions service to check
   * the column's permissions before displaying each column. Below is a pseudo example where you
   * want to show the instance compute host only if the user is an admin. So you'd create a policy
   * rule for checking if the user is an admin and add that check here. Or you'd want to only
   * show the volume column if Cinder (the volume service) is enabled.
   *
   * registry.getResourceType('OS::Nova::Server')
      .tableColumns
      .append({
        id: 'host',
        priority: 1,
        policies: [{rules: [['compute', 'compute:is_admin']]}]
      })
      .append({
        id: 'volumes',
        priority: 2,
        services: "volume"
      })
   *
   * 'policies' may be set to a single object or an array of rules objects.
   *
   * All of the following are examples:
   *
   * policies = { rules: [["identity", "identity:get_project"]] }
   * policies = [{ rules: [["identity", "identity:get_project"]] }, { <rule 2>}]
   *
   * 'services' may by set to a single service type or an array of service types.
   * This may be done inline or may come from an object in scope.
   *
   * All of the following are valid examples:
   *
   * services="network"
   * services=["network"]
   * services=["network", "metering"]
   *
   * 'settings' Additional info. In local_settings.py allows you to specify settings such as:
   *
   * OPENSTACK_HYPERVISOR_FEATURES = {
   *    'can_set_mount_point': True,
   *    'can_set_password': False,
   * }
   *
   * To access a specific setting, use a simplified path where a . (dot)
   * separates elements in the path.  So in the above example, the paths
   * would be:
   *
   * OPENSTACK_HYPERVISOR_FEATURES.can_set_mount_point
   * OPENSTACK_HYPERVISOR_FEATURES.can_set_password
   *
   * The `settings` attribute may be set to a single setting path
   * or an array of setting paths. All of the following are examples:
   *
   * settings="SETTING_GROUP.my_setting_1"
   * settings=["SETTING_GROUP.my_setting_1"]
   * settings=["SETTING_GROUP.my_setting_1", "SETTING_GROUP.my_setting_2"]
   *
   * The desired setting must be listed in one of the two following locations
   * in settings.py or local_settings.py in order for it to be available
   * to the client side for evaluation. If it is not, it will always evaluate
   * to false.
   *
   * REST_API_REQUIRED_SETTINGS
   * REST_API_REQUIRED_SETTINGS
   *
   * This directive currently only supports settings that are set to
   * true or false. So currently, you only need to provide the path to
   * the setting. Future enhancements should allow for alternatively providing
   * an object or array of objects with the path and expected value:
   * {path:"SOME_setting_1", expected:"1.0"}.
   */
  function permissionsDecorator($provide) {
    $provide.decorator('horizon.framework.conf.permissions.service',
      ['$delegate',
        'horizon.app.core.openstack-service-api.policy',
        'horizon.app.core.openstack-service-api.serviceCatalog',
        'horizon.app.core.openstack-service-api.settings',
        decorator]);

    function decorator($delegate, policy, serviceCatalog, settings) {
      var permissionsService = $delegate;

      permissionsService.extendedPermissions = {
        policies: policy.ifAllowed,
        services: serviceCatalog.ifTypeEnabled,
        settings: settings.ifEnabled
      };

      return $delegate;
    }
  }

})();
