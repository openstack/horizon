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
    .directive('hzSettingsToggle', hzSettingsToggle);

  hzSettingsToggle.$inject = [
    'hzPromiseToggleTemplateDirective',
    'horizon.app.core.openstack-service-api.settings'
  ];

  /**
   * @ngdoc directive
   * @name horizon.app.core.cloud-services:directive:hzSettingsToggle
   * @module horizon.app.core.cloud-services
   * @description
   *
   * This is to enable specifying conditional UI in a declarative way.
   * Some UI components should be showing only when some certain settings
   * are enabled on `hzSettingsToggle` service.
   * @example
   *
   ```html
   <div hz-settings-toggle='["something"]'>
   <!-- ui code here -->
   </div>
   ```
   */
  function hzSettingsToggle(hzPromiseToggleTemplate, settingsService) {
    return angular.extend(
        hzPromiseToggleTemplate[0],
        {
          singlePromiseResolver: settingsService.ifEnabled,
          name: 'hzSettingsToggle'
        }
    );
  }

})();
