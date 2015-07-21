(function () {
  'use strict';

  angular
    .module('hz.dashboard', [
      'hz.dashboard.launch-instance',
      'hz.dashboard.tech-debt'
    ])
    .config(config);

  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/';
    $provide.constant('dashboardBasePath', path);
  }

})();
