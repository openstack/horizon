(function () {
  'use strict';

  angular
    .module('horizon.framework', [
      'horizon.framework.conf',
      'horizon.framework.util',
      'horizon.framework.widgets'
    ])
    .constant('horizon.framework.basePath', '/static/framework/')
    .config(frameworkConfiguration);

  frameworkConfiguration.$inject = [
    '$interpolateProvider',
    '$httpProvider',
    '$windowProvider'
  ];

  function frameworkConfiguration($interpolateProvider, $httpProvider, $windowProvider) {
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
    $httpProvider.interceptors.push(redirect);

    function redirect($q) {
      return {
        responseError: function (error) {
          if (error.status === 401) {
            $windowProvider.$get().location.replace('/auth/logout');
          }
          return $q.reject(error);
        }
      };
    }
  }

})();
