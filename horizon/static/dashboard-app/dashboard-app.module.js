/*global angularModuleExtension*/
(function () {
  'use strict';

  angular.module('horizon.dashboard-app', [
    'horizon.framework',
    'horizon.auth',
    'horizon.openstack-service-api',
    'ngCookies'].concat(angularModuleExtension))

    .constant('horizon.dashboard-app.conf', {
      // Placeholders; updated by Django.
      debug: null,  //
      static_url: null,
      ajax: {
        queue_limit: null
      }
    })

    .run([
      'horizon.framework.conf.spinner_options',
      'horizon.dashboard-app.conf',
      'horizon.framework.util.tech-debt.helper-functions',
      '$cookieStore',
      '$http',
      '$cookies',
      function (spinnerOptions, hzConfig, hzUtils, $cookieStore, $http, $cookies) {
        $http.defaults.headers.post['X-CSRFToken'] = $cookies.csrftoken;
        //expose the configuration for horizon legacy variable
        horizon.conf = angular.extend({spinner_options: spinnerOptions}, hzConfig);
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
