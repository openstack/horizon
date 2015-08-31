(function () {
 'use strict';

  var module = angular.module('hz.dashboard', [
    'hz.dashboard.launch-instance',
    'hz.dashboard.workflow'
  ])
    .config(config);

  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/';
    $provide.constant('dashboardBasePath', path);
  }

})();
