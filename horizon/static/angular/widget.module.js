(function () {
  'use strict';

  angular
    .module('hz.widgets', [
      'hz.widget.form',
      'hz.widget.help-panel',
      'hz.widget.wizard',
      'hz.widget.table',
      'hz.widget.modal',
      'hz.widget.modal-wait-spinner',
      'hz.framework.bind-scope',
      'hz.framework.workflow',
      'hz.widget.transfer-table',
      'hz.widget.charts',
      'hz.widget.action-list',
      'hz.widget.metadata-tree',
      'hz.widget.metadata-display',
      'hz.framework.validators'
    ])
    .config(config);

  function config($provide, $windowProvider) {
    var path = $windowProvider.$get().STATIC_URL + 'angular/';
    $provide.constant('basePath', path);
  }

})();
