(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @name hz.framework.bind-scope
   * @description
   *
   * # hz.framework.bind-scope
   *
   * This utility widget supports binding the scope where the directive is
   * instantiated with the transcluded content. This is useful when trying
   * to display transcluded content using the `ngRepeat` scope.
   *
   * | Directives                                                               |
   * |--------------------------------------------------------------------------|
   * | {@link hz.framework.bind-scope.directive:bindScope `bindScope`}          |
   *
   */
  angular.module('hz.framework.bind-scope', [])

  /**
   * @ngdoc directive
   * @name hz.framework.bind-scope.directive:bindScope
   * @element ng-repeat
   * @description
   * The `bindScope` directive injects the scope where it is
   * instantiated into the transclusion function so that the
   * transcluded content is rendered correctly. The content
   * is then append to the element where 'bind-scope-target'
   * is defined.
   *
   * @restrict A
   *
   * @example
   * ```
   * <tr ng-repeat bind-scope>
   *   <td></td>
   *   <td class="detail" bind-scope-target>
   *   </td>
   * </tr>
   * ```
   */
  .directive('bindScope', function() {
    return {
      restrict: 'A',
      link: function(scope, element, attrs, ctrl, transclude) {
        if (transclude) {
          transclude(scope, function(clone) {
            var detailElt = element.find('[bind-scope-target]');
            if (detailElt.length) {
              detailElt.append(clone);
            }
          });
        }
      }
    };
  });

})();