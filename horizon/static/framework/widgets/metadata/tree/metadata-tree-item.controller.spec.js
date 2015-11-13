/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
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

  describe('Metadata Tree Item Controller', function() {
    var ctrl;

    beforeEach(module('horizon.framework.widgets.metadata.tree'));
    beforeEach(inject(function ($controller, $injector) {
      ctrl = $controller('MetadataTreeItemController');
    }));

    it('defines the controller', function() {
      expect(ctrl).toBeDefined();
    });

    it('defines formatErrorMessage', function() {
      expect(ctrl.formatErrorMessage).toBeDefined();
    });

    describe("formatErrorMessage", function() {

      it("returns minimum", function() {
        var item = {leaf: {minimum: "-1"}};
        var error = {min: true};
        ctrl.text = {min: "texmin"};

        expect(ctrl.formatErrorMessage(item, error)).toBe('texmin -1');
      });

      it("returns maximum", function() {
        var item = {leaf: {maximum: "200"}};
        var error = {max: true};
        ctrl.text = {max: "texmax"};

        expect(ctrl.formatErrorMessage(item, error)).toBe('texmax 200');
      });

      it("returns minimum length", function() {
        var item = {leaf: {minLength: "5"}};
        var error = {minlength: true};
        ctrl.text = {minLength: "texminlen"};

        expect(ctrl.formatErrorMessage(item, error)).toBe('texminlen 5');
      });

      it("returns maximum length", function() {
        var item = {leaf: {maxLength: "200"}};
        var error = {maxlength: true};
        ctrl.text = {maxLength: "texmaxlen"};

        expect(ctrl.formatErrorMessage(item, error)).toBe('texmaxlen 200');
      });

      it("returns pattern mismatch/integer", function() {
        var item = {leaf: {type: "integer"}};
        var error = {pattern: true};
        ctrl.text = {integerRequired: "texint"};

        expect(ctrl.formatErrorMessage(item, error)).toBe('texint');
      });

      it("returns pattern mismatch/non-integer", function() {
        var item = {leaf: {type: "other"}};
        var error = {pattern: true};
        ctrl.text = {patternMismatch: "texmismatch"};

        expect(ctrl.formatErrorMessage(item, error)).toBe('texmismatch');
      });

      it("returns number mismatch/integer", function() {
        var item = {leaf: {type: "integer"}};
        var error = {number: true};
        ctrl.text = {integerRequired: "texint"};

        expect(ctrl.formatErrorMessage(item, error)).toBe('texint');
      });

      it("returns number mismatch/non-integer", function() {
        var item = {leaf: {type: "other"}};
        var error = {number: true};
        ctrl.text = {decimalRequired: "texdec"};

        expect(ctrl.formatErrorMessage(item, error)).toBe('texdec');
      });

      it("returns required", function() {
        var error = {required: true};
        ctrl.text = {required: "texreq"};

        expect(ctrl.formatErrorMessage(undefined, error)).toBe('texreq');
      });

      it("returns nothing when nothing for error", function() {
        var error = {};

        expect(ctrl.formatErrorMessage(undefined, error)).toBeUndefined();
      });

    });

  });

})();
