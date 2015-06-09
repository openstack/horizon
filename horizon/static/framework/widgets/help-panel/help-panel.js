(function() {
  'use strict';

  /**
   * @ngdoc directive
   * @name horizon.framework.widgets.help-panel.directive:helpPanel
   * @element
   * @description
   * The `helpPanel` directive provides a help panel that can be
   * hidden or shown by clicking on the help/close icon. By default,
   * the help panel appears on the right side of the parent container.
   *
   * @restrict E
   * @example
   * ```
   * <div class="parent-container">
   *   <help-panel>My Content</help-panel>
   * </div>
   * ```
   */
  angular
    .module('horizon.framework.widgets.help-panel', [])
    .directive('helpPanel', helpPanel);

  helpPanel.$inject = [ 'horizon.framework.widgets.basePath' ];

  function helpPanel(path) {
    return {
      templateUrl: path + 'help-panel/help-panel.html',
      transclude: true
    };
  }

})();
