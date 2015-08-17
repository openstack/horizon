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
    .module('horizon.framework.util.promise-toggle')
    .directive('hzPromiseToggleMock', hzPromiseToggleMock);

  hzPromiseToggleMock.$inject =  [
    'hzPromiseToggleTemplateDirective',
    'mockService'
  ];

  /**
   * @ngdoc directive
   * @name horizon.framework.util.promise-toggle:hzPromiseToggleMock
   * @module horizon.framework.util.promise-toggle
   * @description
   *
   * This allows testing the promise toggle directive in the way
   * that it is intended to be used. It also provides a usage example.
   *
   * @example
   *
   ```html
    <div hz-promize-toggle-mock='["config_drive"]'>
      <div class="checkbox customization-script-source">
        <label>
          <input type="checkbox"
                 ng-model="model.newInstanceSpec.config_drive">
          {$ ::label.configurationDrive $}
        </label>
      </div>
    </div>
   ```
   */
  function hzPromiseToggleMock(hzPromiseToggleTemplateDirective, mockService) {
    return angular.extend(
      hzPromiseToggleTemplateDirective[0],
      {
        singlePromiseResolver: mockService.mockResolver,
        name: 'hzPromiseToggleMock'
      }
    );
  }

})();
