/*
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  angular
    .module('horizon.app.core.cloud-services')
    .directive('hzIfSettings', hzSettingsToggle);

  hzSettingsToggle.$inject = [
    'hzPromiseToggleTemplateDirective',
    'horizon.app.core.openstack-service-api.settings'
  ];

  /**
   * @ngdoc directive
   * @name horizon.app.core.cloud-services:directive:hzIfSettings
   * @module horizon.app.core.cloud-services
   * @description
   *
   * Add this directive to any element containing content which should
   * only be evaluated when the specified settings are enabled in
   * horizon. If the settings are enabled, the content will be evaluated.
   * Otherwise, the content will not be compiled. In addition, the
   * element and everything contained by it will be removed completely,
   * leaving a simple HTML comment.
   *
   * This is evaluated once per page load. In current horizon, this means
   * it will get re-evaluated with events like the user opening another panel,
   * changing logins, or changing their region.
   *
   * local_settings.py allows you to specify settings such as:
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
   * The hz-if-settings attribute may be set to a single setting path
   * or an array of setting paths. All of the following are examples:
   *
   * hz-if-settings='"SETTING_GROUP.my_setting_1"'
   * hz-if-settings='["SETTING_GROUP.my_setting_1"]'
   * hz-if-settings='["SETTING_GROUP.my_setting_1", "SETTING_GROUP.my_setting_2"]'
   *
   * The desired setting must be listed in one of the two following locations
   * in settings.py or local_settings.py in order for it to be available
   * to the client side for evaluation. If it is not, it will always evalute
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
   *
   * @example
   *
   * In the following example, if the
   * OPENSTACK_HYPERVISOR_FEATURES.can_set_mount_point
   * setting is set to false, then the div element with
   * hz-if-settings and all of the elements inside of it will be removed
   * and never evaluated by the angular compiler.
   *
   ```html
   <div hz-if-settings='"OPENSTACK_HYPERVISOR_FEATURES.can_set_mount_point"'>
     <!-- ui code here -->
   </div>
   ```
   */
  function hzSettingsToggle(hzPromiseToggleTemplate, settingsService) {
    return angular.extend(
        hzPromiseToggleTemplate[0],
        {
          singlePromiseResolver: settingsService.ifEnabled,
          name: 'hzIfSettings'
        }
    );
  }

})();
