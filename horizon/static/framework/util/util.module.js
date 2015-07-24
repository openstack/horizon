(function () {
  'use strict';

  angular
    .module('horizon.framework.util', [
      'horizon.framework.util.bind-scope',
      'horizon.framework.util.filters',
      'horizon.framework.util.http',
      'horizon.framework.util.i18n',
      'horizon.framework.util.tech-debt',
      'horizon.framework.util.workflow',
      'horizon.framework.util.validators'
    ])
    .config(config);

  config.$inject = ['$provide', '$windowProvider'];

  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'framework/util/';
    $provide.constant('horizon.framework.util.basePath', path);
  }

})();
