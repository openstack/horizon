(function () {
 'use strict';

  angular.module('hz.widgets', [
    'hz.widget.help-panel',
    'hz.widget.wizard',
    'hz.widget.table',
    'hz.widget.modal',
    'hz.framework.bind-scope',
    'hz.widget.transfer-table',
    'hz.widget.charts',
    'hz.widget.action-list'
  ])
    .constant('basePath', '/static/angular/');

})();
