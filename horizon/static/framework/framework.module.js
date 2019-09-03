/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

(function () {
  'use strict';

  angular
    .module('horizon.framework', [
      'ngRoute',
      'horizon.framework.conf',
      'horizon.framework.util',
      'horizon.framework.widgets'
    ])
    .config(config)
    .run(run)
    .factory('horizon.framework.redirect', redirect)
    .config(registerNotFound)
    .constant('horizon.framework.events', {
      AUTH_ERROR: 'AUTH_ERROR'
    });

  config.$inject = [
    '$injector',
    '$provide',
    '$interpolateProvider',
    '$httpProvider',
    '$windowProvider'
  ];

  function config($injector, $provide, $interpolateProvider, $httpProvider, $windowProvider) {

    var path = $windowProvider.$get().STATIC_URL + 'framework/';
    $provide.constant('horizon.framework.basePath', path);

    // Replacing the default angular symbol
    // allow us to mix angular with django templates
    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');

    // Http global settings for ease of use
    $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
    $httpProvider.defaults.xsrfCookieName = 'csrftoken';
    $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
    $httpProvider.defaults.headers.common['Content-Type'] = 'application/json;charset=utf-8';

    // NOTE(tsufiev): angular-ui/bootstrap v0.11.2 dropdownToggle directive
    // conflicts with the native Bootstrap data-toggle="dropdown" attribute
    // (see https://github.com/angular-ui/bootstrap/issues/2156).
    // This is fixed in 0.13, but before that it'd be valuable to ensure that
    // the same html markup works the same way with both versions of
    // angular-ui/bootstrap (0.11.2 and 0.13). Could be safely deleted once
    // Horizon migrates to angular-ui/bootstra v0.13
    if ($injector.has('dropdownToggleDirective')) {
      $provide.decorator('dropdownToggleDirective', patchDropdowns);
    }

    patchDropdowns.$inject = ['$delegate'];

    function patchDropdowns($delegate) {
      var directive = $delegate[0];
      directive.restrict = 'A';
      return $delegate;
    }

    // Global http error handler
    // if user is not authorized, log user out
    // this can happen when session expires
    $httpProvider.interceptors.push(redirect);
    $httpProvider.interceptors.push(stripAjaxHeaderForCORS);

    stripAjaxHeaderForCORS.$inject = [];
    // Standard CORS middleware used in OpenStack services doesn't expect
    // X-Requested-With header to be set for requests and rejects requests
    // which have it. Since there is no reason to treat Horizon specially when
    // dealing handling CORS requests, it's better for Horizon not to set this
    // header when it sends CORS requests. Detect CORS request by presence of
    // X-Auth-Token headers which normally should be provided because of
    // Keystone authentication.
    function stripAjaxHeaderForCORS() {
      return {
        request: function(config) {
          if ('X-Auth-Token' in config.headers) {
            delete config.headers['X-Requested-With'];
          }
          return config;
        }
      };
    }
  }

  run.$inject = ['$window', '$rootScope'];

  function run($window, $rootScope) {
    $window.recompileAngularContent = recompileAngularContent;

    function recompileAngularContent($element) {
      function explicit($compile) {
        // NOTE(tsufiev): recompiling elements with ng-click directive spawns
        // a new 'click' handler even if there were some, so we need to cleanup
        // existing handlers before doing this.
        $element.find('[ng-click]').off('click');
        $compile($element)($rootScope);
      }
      explicit.$inject = ['$compile'];
      $element.injector().invoke(explicit);
    }
  }

  redirect.$inject = [
    '$q',
    '$rootScope',
    '$window',
    'horizon.framework.events',
    'horizon.framework.widgets.toast.service'
  ];

  function redirect($q, $rootScope, $window, frameworkEvents, toastService) {
    return {
      responseError: function (error) {
        if (error.status === 401) {
          var msg = gettext('Unauthorized. Redirecting to login');
          handleRedirectMessage(msg, $rootScope, $window, frameworkEvents, toastService, true);
        }
        if (error.status === 403) {
          var msg2 = gettext('Forbidden. Insufficient permissions of the requested operation');
          handleRedirectMessage(msg2, $rootScope, $window, frameworkEvents, toastService, false);
        }
        return $q.reject(error);
      },
      notFound: function() {
        $window.location.href = $window.WEBROOT + 'not_found';
      }
    };
  }

  function handleRedirectMessage(
      msg, $rootScope, $window, frameworkEvents, toastService, forceLogout) {
    var toast = toastService.find('error', msg);
    //Suppress the multiple duplicate redirect toast messages.
    if (!toast) {
      toastService.add('error', msg);
      $rootScope.$broadcast(frameworkEvents.AUTH_ERROR, msg);
    }
    if (forceLogout) {
      $window.location.replace($window.WEBROOT + 'auth/logout');
    }
  }

  registerNotFound.$inject = [
    '$routeProvider'
  ];

  /**
   * @name registerNotFound
   * @param {Object} $routeProvider
   * @description Routes to "not_found".
   * @returns {undefined} Returns nothing
   */
  function registerNotFound($routeProvider) {
    // if identifier not specified for "ngdetails"
    $routeProvider.when('/ngdetails/:resourceType', {
      redirectTo: "/not_found"
    });
  }

})();
