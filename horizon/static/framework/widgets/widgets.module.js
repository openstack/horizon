(function () {
  'use strict';

  angular
    .module('horizon.framework.widgets', [
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
    .config(config);

  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'framework/widgets/';
    $provide.constant('horizon.framework.widgets.basePath', path);
  }

})();
