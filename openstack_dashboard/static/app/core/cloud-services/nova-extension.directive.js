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

  angular
    .module('horizon.app.core.cloud-services')
    .directive('novaExtension', novaExtension);

  novaExtension.$inject =  ['horizon.app.core.cloud-services.createDirectiveSpec'];

  /**
   * @ngdoc directive
   * @name horizon.app.core.cloud-services:directive:novaExtension
   * @module horizon.app.core.cloud-services
   * @description
   *
   * This is to enable specifying conditional UI in a declarative way.
   * Some UI components should be showing only when some certain extensions
   * are enabled on `novaExtensions` service.
   *
   * @example
   *
   ```html
    <nova-extension required-extensions='["config_drive"]'>
      <div class="checkbox customization-script-source">
        <label>
          <input type="checkbox"
                 ng-model="model.newInstanceSpec.config_drive">
          {$ ::label.configurationDrive $}
        </label>
      </div>
    </nova-extension>

    <nova-extension required-extensions='["disk_config"]'>
      <div class="form-group disk-partition">
        <label for="launch-instance-disk-partition">
          {$ ::label.diskPartition $}
        </label>
        <select class="form-control"
                id="launch-instance-disk-partition"
                ng-model="model.newInstanceSpec.disk_config"
                ng-options="option.value as option.text for option in diskConfigOptions">
        </select>
      </div>
    </nova-extension>
   ```
   */
  function novaExtension(createDirectiveSpec) {
    return createDirectiveSpec('novaExtensions', 'requiredExtensions');
  }

})();
