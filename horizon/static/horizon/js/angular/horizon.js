/*global angularModuleExtension*/
(function () {
  'use strict';

  var horizon_dependencies = ['hz.conf', 'hz.utils', 'hz.api', 'ngCookies', 'hz.widgets', 'hz.filters'];
  var dependencies = horizon_dependencies.concat(angularModuleExtension);
  angular.module('hz', dependencies)
    .config(['$interpolateProvider', '$httpProvider',
      function ($interpolateProvider, $httpProvider) {

        // Replacing the default angular symbol
        // allow us to mix angular with django templates
        $interpolateProvider.startSymbol('{$');
        $interpolateProvider.endSymbol('$}');

        // Http global settings for ease of use
        $httpProvider.defaults.xsrfHeaderName = 'X-CSRFToken';
        $httpProvider.defaults.xsrfCookieName = 'csrftoken';
        $httpProvider.defaults.headers.common['X-Requested-With'] = 'XMLHttpRequest';
        $httpProvider.defaults.headers.common['Content-Type'] = 'application/json;charset=utf-8';

        // Global http error handler
        // if user is not authorized, log user out
        // this can happen when session expires
        $httpProvider.interceptors.push(function($q) {
          return {
            responseError: function(error) {
              if (error.status === 401){
                window.location.replace('/auth/logout');
              }
              return $q.reject(error);
            }
          };
        });
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
