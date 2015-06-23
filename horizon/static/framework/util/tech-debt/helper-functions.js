(function () {
  'use strict';

  angular
    .module('horizon.framework.util.tech-debt')
    .factory('horizon.framework.util.tech-debt.helper-functions', utils);

  // An example of using the John Papa recommended $inject instead of in-line
  // array syntax
  utils.$inject = ['$rootScope', '$compile'];

  function utils($rootScope, $compile) {
    return {
      capitalize: function (string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
      },
      /*
       Adds commas to any integer or numbers within a string for human display.

       EG:
       horizon.utils.humanizeNumbers(1234); -> "1,234"
       horizon.utils.humanizeNumbers("My Total: 1234"); -> "My Total: 1,234"
       */
      humanizeNumbers: function (number) {
        return number.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
      },

      /*
       Truncate a string at the desired length. Optionally append an ellipsis
       to the end of the string.

       EG:
       horizon.utils.truncate("String that is too long.", 18, true); ->
       "String that is too&hellip;"
       */
      truncate: function (string, size, includeEllipsis) {
        if (string.length > size) {
          if (includeEllipsis) {
            return string.substring(0, (size - 3)) + "&hellip;";
          }

          return string.substring(0, size);
        }

        return string;
      },
      loadAngular: function (element) {
        try {
          $compile(element)($rootScope);
          $rootScope.$apply();
        } catch (err) {}
        /*
         Compilation fails when it could not find a directive,
         fails silently on this, it is an angular behaviour.
         */
      }
    };
  }
}());
