(function () {
 'use strict';

  angular.module('horizon.framework.util', [
    'hz.framework.bind-scope',
    'hz.framework.workflow',
    'hz.framework.validators'
  ])
    .constant('horizon.framework.util.basePath', '/static/framework/util/');

})();
