/* jshint globalstrict: true */
'use strict';

describe('hz.widget.charts module', function () {
  it('should be defined', function () {
    expect(angular.module('hz.widget.charts')).toBeDefined();
  });
});

describe('pie chart directive', function() {

  var $scope, $element;

  beforeEach(module('templates'));
  beforeEach(module('hz'));
  beforeEach(module('hz.widgets'));
  beforeEach(module('hz.widget.charts'));

  beforeEach(inject(function($injector) {
    var $compile = $injector.get('$compile');
    $scope = $injector.get('$rootScope').$new();

    $scope.testData = {
      title: 'Total Instances',
      label: '25%',
      data: [
        { label: 'Current', value: 1, color: '#1f83c6' },
        { label: 'Added', value: 1, color: '#81c1e7' },
        { label: 'Remaining', value: 6, color: '#d1d3d4', hideKey: true }
      ]
    };

    var settings = '{ "innerRadius": 25 }';
    var markup = "<pie-chart chart-data='testData' chart-settings='" + settings + "'></pie-chart>";
    $element = angular.element(markup);
    $compile($element)($scope);

    $scope.$digest();
  }));

  it('should be compiled', function() {
    expect($element.html().trim()).not.toBe('');
  });

  it('should have svg element', function() {
    expect($element.find('svg')).toBeDefined();
  });

  it('should have 3 path elements', function() {
    expect($element.find('path.slice').length).toBe(3);
  });

  it('should have correct colors for slices', function() {
    var slices = $element.find('path.slice');

    var slice1Color = slices[0].style.fill;

    if (slice1Color.indexOf('rgb') === 0) {
      expect(slices[0].style.fill).toBe('rgb(31, 131, 198)');
      expect(slices[1].style.fill).toBe('rgb(129, 193, 231)');
      expect(slices[2].style.fill).toBe('rgb(209, 211, 212)');
    } else {
      expect(slices[0].style.fill).toBe('#1f83c6');
      expect(slices[1].style.fill).toBe('#81c1e7');
      expect(slices[2].style.fill).toBe('#d1d3d4');
    }
  });

  it('should have a correct title "Total Instances (8 Max)"', function() {
    var title = $element.find('.pie-chart-title').text().trim();
    expect(title).toBe('Total Instances (8 Max)');
  });

  it('should have a legend', function() {
    expect($element.find('.pie-chart-legend')).toBeDefined();
  });

  it ('should have correct legend keys and labels', function() {
    var legendKeys = $element.find('.pie-chart-legend .slice-legend');

    var firstKeyLabel = legendKeys[0];
    var secondKeyLabel = legendKeys[1];

    expect(firstKeyLabel.textContent.trim()).toBe('1 Current');
    expect(secondKeyLabel.textContent.trim()).toBe('1 Added');
  });

});