(function () {
 'use strict';

  angular.module('hz.widgets', [
    'hz.widget.help-panel',
    'hz.widget.wizard',
    'hz.widget.table',
    'hz.widget.modal'
  ])
    .constant('basePath', '/static/angular/');

})();
