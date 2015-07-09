(function () {
  'use strict';

  angular
    .module('hz.dashboard', [
      'hz.dashboard.launch-instance'
    ])
    .config(config);

  config.$inject = ['$provide', '$windowProvider'];

  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'dashboard/';
    $provide.constant('dashboardBasePath', path);
  }

})();
