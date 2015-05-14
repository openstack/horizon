(function () {
 'use strict';

  angular.module('horizon.framework.widgets', [
    'hz.widget.form',
    'hz.widget.help-panel',
    'hz.widget.wizard',
    'hz.widget.table',
    'hz.widget.modal',
    'hz.widget.modal-wait-spinner',
    'hz.widget.transfer-table',
    'hz.widget.charts',
    'hz.widget.action-list',
    'hz.widget.metadata-tree',
    'hz.widget.metadata-display',
    'hz.widget.toast'
  ])
    .constant('horizon.framework.widgets.basePath', '/static/framework/widgets/');

})();
