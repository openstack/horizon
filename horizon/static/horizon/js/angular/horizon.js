var horizonApp = angular.module('hz', ['hz.conf', 'hz.utils'])
  .config(['$interpolateProvider', function ($interpolateProvider) {
    $interpolateProvider.startSymbol('{$');
    $interpolateProvider.endSymbol('$}');
  }])
  .run(['hzConfig', 'hzUtils', function (hzConfig, hzUtils) {
    //expose the configuration for horizon legacy variable
    horizon.conf = hzConfig;
    horizon.utils = hzUtils;
  }]);

