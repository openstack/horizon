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

  describe('resource type service', function() {
    var service;

    beforeEach(module('horizon.framework.conf'));

    beforeEach(module(function($provide) {
      $provide.value('horizon.framework.util.extensible.service', angular.noop);
    }));

    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.framework.conf.resource-type-registry.service');
    }));

    it('exists', function() {
      expect(service).toBeDefined();
    });

    it('init calls initScope on item and batch actions', function() {
      var action = { service: { initScope: angular.noop } };
      spyOn(action.service, 'initScope');
      service.getResourceType('newthing').batchActions.push(action);
      service.initActions('newthing', { '$new': function() { return 4; }} );
      expect(action.service.initScope).toHaveBeenCalledWith(4);
    });

    it('init ignores initScope when not present', function() {
      var action = { service: { } };
      service.getResourceType('newthing').batchActions.push(action);
      var returned = service.initActions('newthing', {} );
      // but we got here
      expect(returned).toBeUndefined();
    });

    describe('getResourceType', function() {
      it('returns a new resource type object even without a config', function() {
        var value = service.getResourceType('something');
        expect(value).toBeDefined();
      });

      it('returns a new resource type object', function() {
        var value = service.getResourceType('something', {here: "I am"});
        expect(value).toBeDefined();
      });

      it('takes the given properties', function() {
        var value = service.getResourceType('something', {here: "I am"});
        expect(value.here).toEqual('I am');
      });

      it('has an setProperty function', function() {
        var value = service.getResourceType('something', {here: "I am"});
        expect(value.setProperty).toBeDefined();
      });

      it('can be called multiple times, overlaying values', function() {
        var value = service.getResourceType('something', {here: "I am"});
        service.getResourceType('something', {another: "Thing"});
        expect(value.here).toBe('I am');
        expect(value.another).toBe('Thing');
      });
    });

    describe('label', function() {
      var label;
      beforeEach(function() {
        var value = service.getResourceType('something', {})
          .setProperty('example', {label: gettext("Example")})
          .setProperty('bad_example', {});
        label = value.label;
      });

      it('returns the property name if there is no such property', function() {
        expect(label('not_exist')).toBe('not_exist');
      });

      it('returns the property name if there is no such property label', function() {
        expect(label('bad_example')).toBe('bad_example');
      });

      it('returns the nice label if there is one', function() {
        expect(label('example')).toBe('Example');
      });
    });

    describe('format', function() {
      var format;
      beforeEach(function() {
        var value = service.getResourceType('something', {})
          .setProperty('mapping', {value_mapping: {'a': 'apple', 'j': 'jacks'}})
          .setProperty('func', {value_function: function(x) { return x.replace('a', 'y'); }})
          .setProperty('default-func', {value_mapping: {a: 'apple'},
             value_mapping_default_function: function(x) { return x.replace('i', 'a'); }})
          .setProperty('multi-func', {value_function: [
            function(x) { return x.replace('a', 'y'); },
            function(x) { return x.replace('y', 'x'); }
          ]})
          .setProperty('default', {value_mapping: {},
            value_mapping_default_value: 'Fell Thru'})
          .setProperty('bad_example', {});
        format = value.format;
      });

      it('returns the value if there is no such property', function() {
        expect(format('not_exist', 'apple')).toBe('apple');
      });

      it('returns the value if there is no mapping, function, or default', function() {
        expect(format('bad_example', 'apple')).toBe('apple');
      });

      it('returns the mapped value if there is one', function() {
        expect(format('mapping', 'a')).toBe('apple');
      });

      it('returns the function return value if there is a value', function() {
        expect(format('func', 'apple')).toBe('ypple');
      });

      it('returns the multiple function return value if there is an array', function() {
        expect(format('multi-func', 'apple')).toBe('xpple');
      });

      it('returns the default mapping value if there is no mapping or function', function() {
        expect(format('default', 'apple')).toBe('Fell Thru');
      });

      it('returns the original value if there is no matching mapping & no default', function() {
        expect(format('mapping', 'what')).toBe('what');
      });

      it('returns the value_mapping_default_function result when no matching mapping', function() {
        expect(format('default-func', 'missing')).toBe('massing');
      });
    });

    describe('getName', function() {
      it('returns nothing if names not provided', function() {
        var type = service.getResourceType('something', {});
        expect(type.getName(2)).toBeUndefined();
      });

      it('returns plural if count not provided', function() {
        var type = service.getResourceType('something',
          {names: ['Name', 'Names']});
        expect(type.getName()).toBe('Names');
      });

      it('returns singular if given one', function() {
        var type = service.getResourceType('something', {names: ["Image", "Images"]});
        expect(type.getName(1)).toBe('Image');
      });

      it('returns plural if given two', function() {
        var type = service.getResourceType('something', {names: ["Image", "Images"]});
        expect(type.getName(2)).toBe('Images');
      });
    });

  });

})();
