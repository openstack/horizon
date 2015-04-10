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
          return interpolate(gettext("%s GB"), [input.toString()]);
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
          return interpolate(gettext("%s MB"), [input.toString()]);
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

    /**
     * @ngdoc filter
     * @name decode
     * @description
     * Returns values based on key and given mapping.  If key doesn't exist
     * in given mapping, return key.  This is useful when translations for
     * codes are present.
     */
    .filter('decode', function() {
      return function(input, mapping) {
        var val = mapping[input];
        return angular.isDefined(val) ? val : input;
      };
    })

    /**
     * @ngdoc filter
     * @name bytes
     * @description
     * Returns a human-readable approximation of the input of bytes,
     * converted to a useful unit of measure.  Uses 1024-based notation.
     */
    .filter('bytes', function() {
      return function(input) {
        var kb = 1024;
        var mb = kb*1024;
        var gb = mb*1024;
        var tb = gb*1024;
        if (isNaN(input) || null === input || input < 0) {
           return '';
         } else if (input >= tb) {
           return interpolate(gettext("%s TB"), [Number(input/tb).toFixed(2)]);
         } else if (input >= gb) {
           return interpolate(gettext("%s GB"), [Number(input/gb).toFixed(2)]);
         } else if (input >= mb) {
           return interpolate(gettext("%s MB"), [Number(input/mb).toFixed(2)]);
         } else if (input >= kb) {
           return interpolate(gettext("%s KB"), [Number(input/kb).toFixed(2)]);
         } else {
           return interpolate(gettext("%s bytes"), [Math.floor(input)]);
         }
       };
     })

  /**
   * @ngdoc filter
   * @name itemCount
   * @description
   * Displays translated count in table footer.
   * Takes only finite numbers.
   */
  .filter('itemCount', function() {
    return function(input) {
      var isNumeric = (input !== null && isFinite(input));
      var number = isNumeric ? Math.round(input): 0;
      var count = (number > 0) ? number: 0;
      var format = ngettext('Displaying %s item', 'Displaying %s items', count);
      return interpolate(format, [count]);
    };
  });

}());
