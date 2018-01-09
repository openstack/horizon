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

  describe('schemaForm decorator', function() {
    var decoratorsProvider, sfErrorMessageProvider;

    beforeEach(module('schemaForm'));
    beforeEach(module('templates'));
    beforeEach(inject(function($injector) {
      decoratorsProvider = $injector.get('schemaFormDecorators');
      sfErrorMessageProvider = $injector.get('sfErrorMessage');
    }));

    it('should be defined', function() {
      expect(angular.module('schemaForm')).toBeDefined();
    });

    it('should define messages for all the error codes', function() {
      // We don't need to check the specifics of each message in a test,
      // but we should check they all exist
      var messageCodes = Object.keys(sfErrorMessageProvider.defaultMessages);
      var expectedMessageCodes = [
        '0', '1', '10', '11', '12', '13', '100', '101', '102', '103', '104',
        '105', '200', '201', '202', '300', '301', '302', '303', '304', '400',
        '401', '402', '403', '500', '501', '600', '1000', 'default'
      ];
      expect(messageCodes).toEqual(expectedMessageCodes);
    });

    it('should define all the fields', function() {
      var fields = Object.keys(decoratorsProvider.decorator('bootstrapDecorator'));
      var expectedFields = [
        '__name', 'textarea', 'fieldset', 'array', 'tabarray', 'tabs', 'section',
        'conditional', 'select', 'checkbox', 'checkboxes', 'number',
        'password', 'submit', 'button', 'radios', 'radios-inline', 'radiobuttons',
        'password-confirm', 'help', 'default'
      ];
      expect(fields).toEqual(expectedFields);
    });
  });
})();
