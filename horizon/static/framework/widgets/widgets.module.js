(function () {
  'use strict';

  angular
    .module('horizon.framework.widgets', [
      'horizon.framework.widgets.headers',
      'horizon.framework.widgets.help-panel',
      'horizon.framework.widgets.wizard',
      'horizon.framework.widgets.table',
      'horizon.framework.widgets.modal',
      'horizon.framework.widgets.modal-wait-spinner',
      'horizon.framework.widgets.transfer-table',
      'horizon.framework.widgets.charts',
      'horizon.framework.widgets.action-list',
      'horizon.framework.widgets.metadata',
      'horizon.framework.widgets.toast',
      'horizon.framework.widgets.magic-search',
      'horizon.framework.widgets.load-edit'
    ])
    .config(config);

  config.$inject = ['$provide', '$windowProvider'];

  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'framework/widgets/';
    $provide.constant('horizon.framework.widgets.basePath', path);
  }

})();
