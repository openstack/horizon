(function () {
  'use strict';

  angular
    .module('horizon.framework', [
      'horizon.framework.conf',
      'horizon.framework.util',
      'horizon.framework.widgets'
    ])
    .config(config)
    .run(run);

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

    redirect.$inject = ['$q'];

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

  run.$inject = ['$window', '$rootScope'];

  function run($window, $rootScope) {
    $window.recompileAngularContent = recompileAngularContent;

    function recompileAngularContent() {
      var body = angular.element('body');

      function explicit($compile) {
        $compile(body)($rootScope);
      }
      explicit.$inject = ['$compile'];
      body.injector().invoke(explicit);
    }
  }

})();
