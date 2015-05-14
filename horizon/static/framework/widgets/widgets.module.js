(function () {
 'use strict';

  angular.module('horizon.framework.widgets', [
    'horizon.framework.widgets.help-panel',
    'horizon.framework.widgets.wizard',
    'horizon.framework.widgets.table',
    'horizon.framework.widgets.modal',
    'horizon.framework.widgets.modal-wait-spinner',
    'horizon.framework.widgets.transfer-table',
    'horizon.framework.widgets.charts',
    'horizon.framework.widgets.action-list',
    'horizon.framework.widgets.metadata-tree',
    'horizon.framework.widgets.metadata-display',
    'horizon.framework.widgets.toast'
  ])
    .constant('horizon.framework.widgets.basePath', '/static/framework/widgets/');

})();
