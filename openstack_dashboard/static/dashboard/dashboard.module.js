(function () {
 'use strict';

  var module = angular.module('hz.dashboard', [
    'hz.dashboard.launch-instance'
  ]);

  module.constant('dashboardBasePath', '/static/dashboard/');

})();
