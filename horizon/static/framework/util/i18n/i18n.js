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
    .module('horizon.framework.util.i18n', [])
    .factory('horizon.framework.util.i18n.gettext', getText);

  getText.$inject = ['$window'];

  /**
   * @name horizon.framework.util.i18n.gettext
   * @description
   * Provides a wrapper for translation, using the global 'gettext'
   * function if it is present.  Provides a method that
   * simply returns the input if the expected global 'gettext' is
   * not provided.
   *
   * Ideally once gettext is no longer needed on a global scope,
   * the global ref can be deleted here.  For now that is not possible.
   * Also, if future alternate means were provided, we could put that
   * logic here.
   *
   * This could also be done in the context of the filter, but
   * the approach taken here was to separate business logic
   * (translation) from filters, which are arguably more
   * presentation-oriented.
   */
  function getText($window) {
    // If no global function, revert to just returning given text.
    var gettextFunc = $window.gettext || function (x) {
      return x;
    };

    // Eventually, could delete the window gettext references here,
    // or provide an appropriate method.
    return function () {
      return gettextFunc.apply(this, arguments);
    };
  }
})();
