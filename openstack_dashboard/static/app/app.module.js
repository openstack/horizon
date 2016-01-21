/*
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

/*global horizonPlugInModules*/

(function () {
  'use strict';

  /**
   * Library modules - modules defined in third-party libraries, including
   * angular's extensions.
   */
  var libraryModules = [
    'gettext',
    'lrDragNDrop',
    'ngCookies',
    'ngSanitize',
    'smart-table',
    'ui.bootstrap'
  ];

  /**
   * Horizon's built-in modules, including modules from `framework` components
   * and modules from `openstack_dashboard` application core components.
   */
  var horizonBuiltInModules = [
    'horizon.app.core',
    'horizon.app.tech-debt',
    'horizon.auth',
    'horizon.framework'
  ];

  /**
   * @ngdoc overview
   * @name horizon.app
   * @description
   *
   * # horizon.app
   *
   * Horizon's application level module depends on modules from three
   * sources:
   *
   * 1) Library modules.
   * 2) Horizon's built-in modules.
   * 3) Horizon's plug-in modules.
   */
  angular
    .module('horizon.app', ['ngRoute']
            .concat(libraryModules)
            .concat(horizonBuiltInModules)
            .concat(horizonPlugInModules)
           )
    .config(configHorizon)
    .run(updateHorizon);

  configHorizon.$inject = [
    '$locationProvider',
    '$routeProvider'
  ];

  /**
   * Configure the Horizon Angular Application.
   * This sets up the $locationProvider Service to use HTML5 Mode and
   * the Hash Prefix to use when it is not supported.
   *
   * It also sets the default Angular route which will apply if
   * a link is clicked that doesn't match any current Angular route.
   *
   */
  function configHorizon($locationProvider, $routeProvider) {
    if (angular.element('base').length === 1) {
      $locationProvider.html5Mode(true).hashPrefix('!');

      $routeProvider
        .otherwise({
          template: '',
          controller: 'RedirectController'
        });
    }
  }

  updateHorizon.$inject = [
    'gettextCatalog',
    'horizon.framework.conf.spinner_options',
    'horizon.framework.util.tech-debt.helper-functions',
    '$cookieStore',
    '$http',
    '$cookies'
  ];

  function updateHorizon(
    gettextCatalog,
    spinnerOptions,
    hzUtils,
    $cookieStore,
    $http,
    $cookies
  ) {

    $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;

    // expose the legacy utils module
    horizon.utils = hzUtils;

    horizon.conf.spinner_options = spinnerOptions;

    horizon.cookies = angular.extend({}, $cookieStore, {
      put: put,
      getRaw: getRaw
    });

    // rewire the angular-gettext catalog to use django catalog
    gettextCatalog.setCurrentLanguage(horizon.languageCode);
    gettextCatalog.setStrings(horizon.languageCode, django.catalog);

    /*
     * cookies are updated at the end of current $eval, so for the horizon
     * namespace we need to wrap it in a $apply function.
     */
    function put(key, value) {
      angular.element('body').scope().$apply(function () {
        $cookieStore.put(key, value);
      });
    }

    function getRaw(key) {
      return $cookies[key];
    }
  }

}());
