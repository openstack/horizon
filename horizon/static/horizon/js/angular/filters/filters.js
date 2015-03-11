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
   * @name hz.filters
   * @description
   * hz.filters provides common filters to be used within Horizon.
   *
   */
  angular.module('hz.filters', [])

    /**
     * @ngdoc filter
     * @name yesno
     * @description
     * Evaluates given input as boolean and returns translation
     * of 'Yes' and 'No' for true/false respectively.
     */
    .filter('yesno', function() {
      return function(input) {
        return (input ? gettext("Yes") : gettext("No"));
      };
    })

    /**
     * @ngdoc filter
     * @name gb
     * @description
     * Expects numeric value and suffixes translated 'GB' with spacing.
     * Returns empty string if input is not a number or is null.
     */
    .filter('gb', function() {
      return function(input) {
        if (isNaN(input) || null === input) {
          return '';
        } else {
          return input.toString() + " " + gettext("GB");
        }
      };
    })

    /**
     * @ngdoc filter
     * @name mb
     * @description
     * Expects numeric value and suffixes translated 'MB' with spacing.
     * Returns empty string if input is not a number or is null.
     */
    .filter('mb', function() {
      return function(input) {
        if (isNaN(input) || null === input) {
          return '';
        } else {
          return input.toString() + " " + gettext("MB");
        }
      };
    })

    /**
     * @ngdoc filter
     * @name title
     * @description
     * Capitalizes leading characters of individual words.
     */
    .filter('title', function() {
      return function(input) {
        if (typeof input !== 'string') {
          return input;
        }
        return input.replace(/(?:^|\s)\S/g, function(a) {
          return a.toUpperCase();
        });
      };
    })

    /**
     * @ngdoc filter
     * @name noUnderscore
     * @description
     * Replaces all underscores with spaces.
     */
    .filter('noUnderscore', function() {
      return function(input) {
        if (typeof input !== 'string') {
          return input;
        }
        return input.replace(/_/g, ' ');
      };
    })

  ;
}());
