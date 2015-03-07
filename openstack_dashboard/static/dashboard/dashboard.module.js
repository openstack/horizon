(function () {
 'use strict';

  var module = angular.module('hz.dashboard', [
    'hz.dashboard.launch-instance',
    'hz.dashboard.workflow'
  ]);

  module.constant('dashboardBasePath', '/static/dashboard/');

})();
