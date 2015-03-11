(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @name hz.widget.form
   *
   * # hz.widget.form
   *
   * The `hz.widget.form` provides form directives and services.
   *
   * | Components                                               |
   * |----------------------------------------------------------|
   * | {@link hz.widget.form.hzPasswordMatch `hzPasswordMatch`} |
   *
   */
  var app = angular.module('hz.widget.form', []);

  /**
   * @ngdoc directive
   * @name hzPasswordMatch
   *
   * @description
   * A directive to ensure that password matches.
   * Changing the password or confirmation password triggers a validation check.
   * However, only the confirmation password will show an error if match is false.
   * The goal is to check that confirmation password matches the password,
   * not whether the password matches the confirmation password.
   * The behavior here is NOT bi-directional.
   *
   * @requires
   * ng-model - model for confirmation password
   *
   * @scope
   * hzPasswordMatch - form model to validate against
   *
   * @example:
   * <form name="form">
   *  <input type='password' id="psw" ng-model="user.psw" name="psw">
   *  <input type='password' ng-model="user.cnf" hz-password-match="form.psw">
   * </form>
   *
   * Note that id and name are required for the password input.
   * This directive uses the form model and id for validation check.
   */
  app.directive('hzPasswordMatch', function(){
    return {
      restrict: 'A',
      require: 'ngModel',
      scope: { pw: '=hzPasswordMatch' },
      link: function(scope, element, attr, ctrl){

        // helper function to check that password matches
        function passwordCheck(){
          scope.$apply(function(){
            var match = (ctrl.$modelValue === scope.pw.$modelValue);
            ctrl.$setValidity('match', match);
          });
        }

        // this ensures that typing in either input
        // will trigger the password match
        var pwElement = $('#'+scope.pw.$name);
        pwElement.on('keyup change', passwordCheck);
        element.on('keyup change', passwordCheck);

      } // end of link
    }; // end of return
  }); // end of directive

})();
