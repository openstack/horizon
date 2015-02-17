/*global angularModuleExtension*/
(function () {
  'use strict';

  var horizon_dependencies = ['hz.conf', 'hz.utils', 'hz.api', 'ngCookies', 'hz.widgets'];
  var dependencies = horizon_dependencies.concat(angularModuleExtension);
  angular.module('hz', dependencies)
    .config(['$interpolateProvider', '$httpProvider',
      function ($interpolateProvider, $httpProvider) {
        $interpolateProvider.startSymbol('{$');
        $interpolateProvider.endSymbol('$}');
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
        $httpProvider.defaults.headers.common['Content-Type'] = 'application/json;charset=utf-8';
      }])
    .run(['hzConfig', 'hzUtils', '$cookieStore', '$http', '$cookies',
      function (hzConfig, hzUtils, $cookieStore, $http, $cookies) {
        $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
        //expose the configuration for horizon legacy variable
        horizon.conf = hzConfig;
        horizon.utils = hzUtils;
        angular.extend(horizon.cookies = {}, $cookieStore);
        horizon.cookies.put = function (key, value) {
          //cookies are updated at the end of current $eval, so for the horizon
          //namespace we need to wrap it in a $apply function.
          angular.element('body').scope().$apply(function () {
            $cookieStore.put(key, value);
          });
        };
        horizon.cookies.getRaw = function (key) {
          return $cookies[key];
        };
      }]);
}());
