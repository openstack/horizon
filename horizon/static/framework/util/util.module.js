(function () {
 'use strict';

  angular.module('horizon.framework.util', [
    'horizon.framework.util.bind-scope',
    'horizon.framework.util.filters',
    'horizon.framework.util.form',
    'horizon.framework.util.i18n',
    'horizon.framework.util.tech-debt',
    'horizon.framework.util.workflow',
    'horizon.framework.util.validators'
  ])
    .constant('horizon.framework.util.basePath', '/static/framework/util/');

})();
