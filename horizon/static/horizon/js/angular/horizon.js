var horizonApp = angular.module('horizonApp', [])
  .config(function($interpolateProvider) {
    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');
  })
  .constant('horizon', horizon);
