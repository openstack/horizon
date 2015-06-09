/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the 'License');
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an 'AS IS' BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function () {
  'use strict';

  angular
    .module('hz.dashboard.launch-instance', [
      'ngSanitize'
    ])
    .constant('hz.dashboard.launch-instance.modal-spec', {
      backdrop: 'static',
      controller: 'ModalContainerController',
      template: '<wizard ng-controller="LaunchInstanceWizardController"></wizard>',
      windowClass: 'modal-dialog-wizard'
    })

    /**
     * @name hz.dashboard.launch-instance.boot-source-types
     * @description Boot source types
     */
    .constant('hz.dashboard.launch-instance.boot-source-types', {
      IMAGE: 'image',
      INSTANCE_SNAPSHOT: 'snapshot',
      VOLUME: 'volume',
      VOLUME_SNAPSHOT: 'volume_snapshot'
    })

    /**
     * @ngdoc filter
     * @name diskFormat
     * @description
     * Expects object and returns disk_format property value.
     * Returns empty string if input is null or not an object.
     * Uniquely required for the source step implementation of transfer tables
     */
    .filter('diskFormat', diskFormat);

  function diskFormat() {
    return filter;

    function filter(input) {
      if (input === null || !angular.isObject(input) ||
        angular.isUndefined(input.disk_format) || input.disk_format === null) {
        return '';
      } else {
        return input.disk_format.toUpperCase();
      }
    }
  }

})();
