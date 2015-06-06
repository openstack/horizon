(function () {
  'use strict';

  angular.module('hz.dashboard', [
    'hz.dashboard.launch-instance',
    'hz.dashboard.tech-debt',
    'hz.dashboard.workflow'
  ])

  .constant('dashboardBasePath', '/static/dashboard/');

})();
