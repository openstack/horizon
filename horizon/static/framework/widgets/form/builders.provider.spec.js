/*
 *    (c) Copyright 2016 Cisco Systems
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function() {
  'use strict';

  describe('hzBuilderProvider', function() {
    var provider, $compile, $scope, args, element, elementTwo;

    var html = "<div><ul><li></li></ul><div class='tab-content'></div></div>";
    var htmlTwo = "<div class='test'></div>";

    beforeEach(module('schemaForm'));

    beforeEach(inject(function($injector) {
      $scope = $injector.get('$rootScope').$new();
      $compile = $injector.get('$compile');
      provider = $injector.get('hzBuilder');
      element = $compile(html)($scope);
      elementTwo = $compile(htmlTwo)($scope);
      $scope.$apply();

      args = { form:
        { tabs: [
          { "title": "tabZero", "items": [ { "title": "item", "required": true } ] },
          { "title": "tabOne", "condition": true, "items": [] },
          { "title": "tabTwo", "condition": false, "items": [] }
        ]},
        fieldFrag: element[0],
        build: function() {
          return elementTwo[0];
        }
      };
    }));

    it('should correctly build tabs', function() {
      provider.tabsBuilder(args);

      expect(element[0].querySelector('li').getAttribute("ng-if")).toBeDefined();
      expect(
        element[0].querySelector('.tab-content').querySelector('div').getAttribute("ng-show")
      ).toBe('model.tabs.selected === 0');
      expect(
        element[0].querySelector('.tab-content').querySelector('div').getAttribute("ng-if")
      ).toBe('true');
      expect(args.form.tabs[0].required).toBe(true);
      expect(args.form.tabs[1].required).not.toBeDefined();
      expect(args.form.tabs[2].required).not.toBeDefined();
    });
  });
})();
