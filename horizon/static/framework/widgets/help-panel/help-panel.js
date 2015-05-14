(function () {
  'use strict';

  angular.module('hz.widget.help-panel', [])
    .directive('helpPanel', ['horizon.framework.widgets.basePath',
      function (path) {
        return {
          templateUrl: path + 'help-panel/help-panel.html',
          transclude: true
        };
      }
    ]);
})();
