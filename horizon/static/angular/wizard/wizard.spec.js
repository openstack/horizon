'use strict';

describe('hz.widget.wizard module', function () {
  it('should have been defined".', function () {
    expect(angular.module('hz.widget.wizard')).toBeDefined();
  });
});

describe('wizard directive', function () {
  var $compile,
      $scope;

  beforeEach(module('templates'));
  beforeEach(module('hz'));
  beforeEach(module('hz.widgets'));
  beforeEach(module('hz.widget.wizard'));
  beforeEach(inject(function ($injector) {
    $scope = $injector.get('$rootScope').$new();
    $compile = $injector.get('$compile');
  }));

  it('should be compiled', function () {
    var element = $compile('<wizard>some text</wizard>')($scope);
    $scope.$digest();
    expect(element.html().trim()).not.toBe('some text');
  });

  it('should have empty title by default', function () {
    var element = $compile('<wizard></wizard>')($scope);
    $scope.workflow = {};
    $scope.$digest();
    expect(element[0].querySelector('.title').innerText).toBe('');
  });

  it('should have title if it is specified by workflow', function () {
    var titleText = 'Some title';
    var element = $compile('<wizard></wizard>')($scope);
    $scope.workflow = {};
    $scope.workflow.title = titleText;
    $scope.$digest();
    expect(element[0].querySelector('.title').innerText).toBe(titleText);
  });

  it('should have no steps if no steps defined', function () {
    var element = $compile('<wizard></wizard>')($scope);
    $scope.workflow = {};
    $scope.$digest();
    expect(element[0].querySelectorAll('.step').length).toBe(0);
  });

  it('should have 3 steps if 3 steps defined', function () {
    var element = $compile('<wizard></wizard>')($scope);
    $scope.workflow = {
      steps: [ {}, {}, {} ]
    };
    $scope.$digest();
    expect(element[0].querySelectorAll('.step').length).toBe(3);
  });

  it('should have no nav items if no steps defined', function () {
    var element = $compile('<wizard></wizard>')($scope);
    $scope.workflow = {};
    $scope.$digest();
    expect(element[0].querySelectorAll('.nav-item').length).toBe(0);
  });

  it('should have 3 nav items if 3 steps defined', function () {
    var element = $compile('<wizard></wizard>')($scope);
    $scope.workflow = {
      steps: [ {}, {}, {} ]
    };
    $scope.$digest();
    expect(element[0].querySelectorAll('.nav-item').length).toBe(3);
  });

  it('should navigate correctly', function () {
    var element = $compile('<wizard></wizard>')($scope);
    $scope.workflow = {
      steps: [ {}, {}, {} ]
    };

    $scope.$digest();
    expect($scope.currentIndex).toBe(0);
    expect(element[0].querySelectorAll('.step')[0].classList.contains('ng-hide')).toBe(false);
    expect(element[0].querySelectorAll('.step')[1].classList.contains('ng-hide')).toBe(true);
    expect(element[0].querySelectorAll('.step')[2].classList.contains('ng-hide')).toBe(true);
    expect(element[0].querySelectorAll('.nav-item')[0].classList.contains('current')).toBe(true);
    expect(element[0].querySelectorAll('.nav-item')[1].classList.contains('current')).toBe(false);
    expect(element[0].querySelectorAll('.nav-item')[2].classList.contains('current')).toBe(false);

    $scope.switchTo(1);
    $scope.$digest();
    expect($scope.currentIndex).toBe(1);
    expect(element[0].querySelectorAll('.step')[0].classList.contains('ng-hide')).toBe(true);
    expect(element[0].querySelectorAll('.step')[1].classList.contains('ng-hide')).toBe(false);
    expect(element[0].querySelectorAll('.step')[2].classList.contains('ng-hide')).toBe(true);
    expect(element[0].querySelectorAll('.nav-item')[0].classList.contains('current')).toBe(false);
    expect(element[0].querySelectorAll('.nav-item')[1].classList.contains('current')).toBe(true);
    expect(element[0].querySelectorAll('.nav-item')[2].classList.contains('current')).toBe(false);

    $scope.switchTo(2);
    $scope.$digest();
    expect($scope.currentIndex).toBe(2);
    expect(element[0].querySelectorAll('.step')[0].classList.contains('ng-hide')).toBe(true);
    expect(element[0].querySelectorAll('.step')[1].classList.contains('ng-hide')).toBe(true);
    expect(element[0].querySelectorAll('.step')[2].classList.contains('ng-hide')).toBe(false);
    expect(element[0].querySelectorAll('.nav-item')[0].classList.contains('current')).toBe(false);
    expect(element[0].querySelectorAll('.nav-item')[1].classList.contains('current')).toBe(false);
    expect(element[0].querySelectorAll('.nav-item')[2].classList.contains('current')).toBe(true);
  });

  it('should not show back button in step 1/3', function () {
    var element = $compile('<wizard></wizard>')($scope);
    $scope.workflow = {
      steps: [{}, {}, {}]
    };
    $scope.$digest();
    expect(element[0].querySelector('button.back').classList.contains('ng-hide')).toBe(true);
    expect(element[0].querySelector('button.next').classList.contains('ng-hide')).toBe(false);
  });

  it('should show both back and next button in step 2/3', function () {
    var element = $compile('<wizard></wizard>')($scope);
    $scope.workflow = {
      steps: [{}, {}, {}]
    };
    $scope.$digest();
    $scope.switchTo(1);
    $scope.$digest();
    expect(element[0].querySelector('button.back').classList.contains('ng-hide')).toBe(false);
    expect(element[0].querySelector('button.next').classList.contains('ng-hide')).toBe(false);
  });

  it('should not show next button in step 3/3', function () {
    var element = $compile('<wizard></wizard>')($scope);
    $scope.workflow = {
      steps: [{}, {}, {}]
    };
    $scope.$digest();
    $scope.switchTo(2);
    $scope.$digest();
    expect(element[0].querySelector('button.back').classList.contains('ng-hide')).toBe(false);
    expect(element[0].querySelector('button.next').classList.contains('ng-hide')).toBe(true);
  });

  it('should have finish button disabled if wizardForm is invalid', function () {
    var element = $compile('<wizard></wizard>')($scope);
    $scope.wizardForm = { };
    $scope.$digest();
    $scope.wizardForm.$invalid = true;
    $scope.$digest();
    expect(element[0].querySelector('button.finish').hasAttribute('disabled')).toBe(true);
  });

  it('should have finish button enabled if wizardForm is valid', function () {
    var element = $compile('<wizard></wizard>')($scope);
    $scope.wizardForm = { };
    $scope.$digest();
    $scope.wizardForm.$invalid = false;
    $scope.$digest();
    expect(element[0].querySelector('button.finish').hasAttribute('disabled')).toBe(false);
  });

  it('should show error message after calling method showError', function () {
    var errorMessage = 'some error message';
    var element = $compile('<wizard></wizard>')($scope);
    $scope.$digest();
    $scope.showError(errorMessage);
    $scope.$digest();
    expect(element[0].querySelector('.error-message').textContent).toBe(errorMessage);
  });

});
