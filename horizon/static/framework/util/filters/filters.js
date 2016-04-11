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
    .module('horizon.framework.util.filters')
    .filter('yesno', yesNoFilter)
    .filter('gb', gbFilter)
    .filter('mb', mbFilter)
    .filter('title', titleFilter)
    .filter('noUnderscore', noUnderscoreFilter)
    .filter('noValue', noValueFilter)
    .filter('noName', noNameFilter)
    .filter('decode', decodeFilter)
    .filter('bytes', bytesFilter)
    .filter('itemCount', itemCountFilter)
    .filter('toIsoDate', toIsoDateFilter)
    .filter('limit', limitFilter);

  /**
   * @ngdoc filter
   * @name yesno
   * @description
   * Evaluates given input for standard truthiness and returns translation
   * of 'Yes' and 'No' for true/false respectively.
   */
  yesNoFilter.$inject = ['horizon.framework.util.i18n.gettext'];
  function yesNoFilter(gettext) {
    return function (input) {
      return input ? gettext("Yes") : gettext("No");
    };
  }

  /**
   * @ngdoc filter
   * @name gb
   * @description
   * Expects numeric value and suffixes translated 'GB' with spacing.
   * Returns empty string if input is not a number or is null.
   */
  function gbFilter() {
    return function (input) {
      var tb = 1024;

      if (isNaN(input) || null === input) {
        return '';
      } else if (input >= tb) {
        return interpolate(gettext("%s TB"), [parseFloat(Number(input / tb).toFixed(2))]);
      } else if (input === '') {
        return interpolate(gettext("0 GB"));
      } else {
        return interpolate(gettext("%s GB"), [input.toString()]);
      }
    };
  }

  /**
   * @ngdoc filter
   * @name mb
   * @description
   * Expects numeric value and suffixes translated 'MB' with spacing.
   * Returns empty string if input is not a number or is null.
   */
  function mbFilter() {
    return function (input) {
      var gb = 1024;

      if (isNaN(input) || null === input) {
        return '';
      } else if (input >= gb) {
        return interpolate(gettext("%s GB"), [parseFloat(Number(input / gb).toFixed(2))]);
      } else if (input === '') {
        return interpolate(gettext("0 MB"));
      } else {
        return interpolate(gettext("%s MB"), [input.toString()]);
      }
    };
  }

  /**
   * @ngdoc filter
   * @name title
   * @description
   * Capitalizes leading characters of individual words.
   */
  function titleFilter() {
    return function (input) {
      if (!angular.isString(input)) {
        return input;
      }
      return input.replace(/(?:^|\s)\S/g, function (a) {
        return a.toUpperCase();
      });
    };
  }

  /**
   * @ngdoc filter
   * @name noUnderscore
   * @description
   * Replaces all underscores with spaces.
   */
  function noUnderscoreFilter() {
    return function (input) {
      if (!angular.isString(input)) {
        return input;
      }
      return input.replace(/_/g, ' ');
    };
  }

  /**
   * @ngdoc filter
   * @name noValue
   * @description
   * Replaces null / undefined / empty string with translated '-' or the optional
   * default value provided.
   */
  function noValueFilter() {
    return function (input, def) {
      if (input === null || angular.isUndefined(input) ||
        (angular.isString(input) && '' === input.trim())) {
        return def || gettext('-');
      } else {
        return input;
      }
    };
  }

  /**
   * @ngdoc filter
   * @name noName
   * @description
   * Replaces null / undefined / empty string with translated 'None'.
   */
  function noNameFilter() {
    return function (input) {
      return input && angular.isString(input) ? input : gettext('None');
    };
  }

  /**
   * @ngdoc filter
   * @name decode
   * @description
   * Returns values based on key and given mapping.  If key doesn't exist
   * in given mapping, return key.  This is useful when translations for
   * codes are present.
   */
  function decodeFilter() {
    return function (input, mapping) {
      var val = mapping[input];
      return angular.isDefined(val) ? val : input;
    };
  }

  /**
   * @ngdoc filter
   * @name bytes
   * @description
   * Returns a human-readable approximation of the input of bytes,
   * converted to a useful unit of measure.  Uses 1024-based notation.
   */
  function bytesFilter() {
    return function (input) {
      var kb = 1024;
      var mb = kb * 1024;
      var gb = mb * 1024;
      var tb = gb * 1024;
      if (isNaN(input) || null === input || input < 0) {
        return '';
      } else if (input >= tb) {
        return interpolate(gettext("%s TB"), [Number(input / tb).toFixed(2)]);
      } else if (input >= gb) {
        return interpolate(gettext("%s GB"), [Number(input / gb).toFixed(2)]);
      } else if (input >= mb) {
        return interpolate(gettext("%s MB"), [Number(input / mb).toFixed(2)]);
      } else if (input >= kb) {
        return interpolate(gettext("%s KB"), [Number(input / kb).toFixed(2)]);
      } else {
        return interpolate(gettext("%s bytes"), [Math.floor(input)]);
      }
    };
  }

  /**
   * @ngdoc filter
   * @name itemCount
   * @description
   * Displays translated count in table footer.
   * Input should be the number shown; an optional parameter specifies how
   * large the total set is regardless of the number shown.
   */
  function itemCountFilter() {

    function ensureNonNegative(input) {
      var isNumeric = (input !== null && isFinite(input));
      var number = isNumeric ? Math.round(input) : 0;
      return (number > 0) ? number : 0;
    }

    return function (input, totalInput) {
      var format;
      var count = ensureNonNegative(input);
      if (angular.isUndefined(totalInput)) {
        format = ngettext('Displaying %s item', 'Displaying %s items', count);
        return interpolate(format, [count]);
      } else {
        var total = ensureNonNegative(totalInput);
        format = gettext('Displaying %(count)s of %(total)s items');
        return interpolate(format, {count: count, total: total}, true);
      }
    };
  }

  /**
   * @ngdoc filter
   * @name toISO8610DateFormat
   * @description
   * Converts the string date into ISO-8610 format, which adds proper UTC
   * timezone identifier.
   */
  function toIsoDateFilter() {
    return function(input) {
      return new Date(input).toISOString();
    };
  }

  /**
   * @ngdoc filter
   * @name limit
   * @description
   * If input is a number greater than or equal to zero, returns the number. Otherwise
   * returns the optional string argument or "Unlimited". Use for number values where
   * anything negative has a special meaning, such as limits where -1 typically means
   * unlimited.
   */
  limitFilter.$inject = ['horizon.framework.util.i18n.gettext'];
  function limitFilter(gettext) {
    return function (input, value) {
      return angular.isNumber(input) && input >= 0 ? input : value || gettext('Unlimited');
    };
  }

})();
