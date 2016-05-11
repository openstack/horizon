/**
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
    .module('horizon.app.core.images')
    .filter('imageStatus', imageStatusFilter);

  imageStatusFilter.$inject = [
    'horizon.framework.util.i18n.gettext'
  ];

  function imageStatusFilter(gettext) {
    var imageStatuses = {
      'active': gettext('Active'),
      'saving': gettext('Saving'),
      'queued': gettext('Queued'),
      'pending_delete': gettext('Pending Delete'),
      'killed': gettext('Killed'),
      'deleted': gettext('Deleted')
    };

    return filter;

    /**
     * @ngdoc filter
     * @name imageStatusFilter
     * @param {string} input - The status code
     * @description
     * Takes raw image status from the API and returns the user friendly status.
     * @returns {string} The user-friendly status
     */
    function filter(input) {
      var result = imageStatuses[input];
      return angular.isDefined(result) ? result : input;
    }
  }

}());
