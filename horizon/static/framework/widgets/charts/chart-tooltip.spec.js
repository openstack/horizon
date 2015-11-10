/*
 * (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function () {
  'use strict';

  describe('chartTooltip directive', function () {
    var $element, $scope;

    beforeEach(module('templates'));
    beforeEach(module('horizon.framework'));

    beforeEach(inject(function (_$compile_, _$rootScope_) {
      var $compile = _$compile_;
      $scope = _$rootScope_.$new();

      $scope.tooltipData = {
        enabled: true,
        label: 'Applied',
        value: 'this is my amazing value',
        icon: 'fa-square',
        iconColor: '#333333',
        style: {left: '10px', top: '12px'}
      };

      var markup = '<chart-tooltip tooltip-data="tooltipData"></chart-tooltip>';
      $element = angular.element(markup);
      $compile($element)($scope);
      $scope.$apply();
    }));

    it('compiles', function () {
      expect($element.html().trim()).not.toBe('');
    });

    it('contains the label', function () {
      expect($element.find('.tooltip-key').last().text()).toContain('Applied');
    });

    it('contains the value', function () {
      expect($element.text()).toContain('this is my amazing value');
    });

    it('enables correctly', function () {
      expect($element.find('div').hasClass('tooltip-enabled')).toBe(true);
    });

    it('disables correctly', function () {
      $scope.tooltipData.enabled = false;
      $scope.$apply();
      expect($element.find('div').hasClass('tooltip-enabled')).toBe(false);
    });

    it('apply the correct style', function () {
      var outerDiv = $element.find('div');
      expect(outerDiv[0].style.left).toBe("10px");
      expect(outerDiv[0].style.top).toBe("12px");
      // There shouldn't be anything other than left and top in the style.
      expect(outerDiv[0].style.length).toBe(2);
    });

    it('has the correct icon', function () {
      var iconSpan = $element.find('span.fa');
      expect(iconSpan.hasClass('fa-square')).toBe(true);
    });

    it('has the correct icon color', function () {
      var iconSpan = $element.find('span.fa');
      var styleColor = iconSpan[0].style.color;
      if (styleColor.indexOf('rgb') === 0) {
        expect(styleColor).toBe('rgb(51, 51, 51)');
      } else {
        expect(styleColor).toBe('#333333');
      }
    });
  });
})();
