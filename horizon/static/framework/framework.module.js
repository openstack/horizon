(function () {
 'use strict';

  angular.module('horizon.framework', [
    'horizon.framework.util',
    'horizon.framework.widgets'
  ])
    .constant('horizon.framework.basePath', '/static/framework/');

})();
