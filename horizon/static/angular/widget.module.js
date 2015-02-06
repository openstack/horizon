(function () {
 'use strict';

  angular.module('hz.widgets', [
    'hz.widget.help-panel',
    'hz.widget.wizard'
  ])
    .constant('basePath', '/static/angular/');

})();
