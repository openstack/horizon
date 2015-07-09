(function () {
  'use strict';

  angular.module('hz.dashboard', [
    'hz.dashboard.launch-instance',
    'hz.dashboard.tech-debt'
  ])

  .constant('dashboardBasePath', '/static/dashboard/');

})();
