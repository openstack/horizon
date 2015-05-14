(function () {
  'use strict';

  angular.module('horizon.framework.widgets.help-panel', [])
    .directive('helpPanel', ['horizon.framework.widgets.basePath',
      function (path) {
        return {
          templateUrl: path + 'help-panel/help-panel.html',
          transclude: true
        };
      }
    ]);
})();
