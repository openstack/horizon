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
  "use strict";

  describe('magic-search service', function () {
    var service;

    beforeEach(module("horizon.framework.widgets.magic-search"));
    beforeEach(inject(function($injector) {
      service = $injector.get('horizon.framework.widgets.magic-search.service');
    }));

    it('should have been defined', function () {
      expect(service).toBeDefined();
    });

    describe("getFacet", function() {
      it("produces the expected output", function() {
        expect(service.getFacet('abc', 'def', 'type-label', 'option-label'))
          .toEqual({'name': 'abc=def', 'label': ['type-label', 'option-label']});
      });
    });

    describe("getTextFacet", function() {
      it("produces the expected output", function() {
        expect(service.getTextFacet('abc', 'type-label'))
          .toEqual({'name': 'text=abc', 'label': ['type-label', 'abc']});
      });
    });

    describe('getEventCode', function() {

      it("looks in evt.which", function() {
        var evt = {which: 42};
        expect(service.getEventCode(evt)).toBe(42);
      });

      it("looks in evt.keyCode", function() {
        var evt = {keyCode: 42};
        expect(service.getEventCode(evt)).toBe(42);
      });

      it("looks in evt.charCode", function() {
        var evt = {charCode: 42};
        expect(service.getEventCode(evt)).toBe(42);
      });

      it("returns undefined if no code set", function() {
        var evt = {};
        expect(service.getEventCode(evt)).toBeUndefined();
      });
    });

    describe('getFacetChoice', function() {

      it("copies facets", function() {
        var input = {a: 'apple'};
        var output = service.getFacetChoice(input);
        expect(output.a).toBe('apple');
      });

      it("copies facets' options", function() {
        var input = {a: 'apple', options: [{b: 'badwolf'}]};
        var output = service.getFacetChoice(input);
        expect(output.a).toBe('apple');
        expect(output.options[0].b).toBe('badwolf');
      });

    });

    describe('getQueryPattern', function() {

      it("returns an empty query if nothing in input", function() {
        expect(service.getQueryPattern([])).toBe('');
      });

      it("returns proper values", function() {
        expect(service.getQueryPattern([{name: 'mytext'}])).toBe('mytext');
        expect(service.getQueryPattern([{name: 'nothing'}, {name: 'mytext'}]))
          .toBe('nothing&mytext');
      });

      it("doesn't process items with name starting with 'text'", function() {
        expect(service.getQueryPattern([{name: 'nothing'}, {name: 'mytext'},
          {name: 'textbad'}])).toBe('nothing&mytext');
      });
    });

    describe('removeFacetChoice', function() {

      it("removes items with the given name", function() {
        var target = [{name: 'me'}, {name: 'me'}, {name: 'notme'}];
        var remove = "me";
        service.removeFacetChoice(remove, target);
        expect(target).toEqual([{name: 'notme'}]);
      });
    });

    describe("getMatchingOptions", function() {

      it("filters properly", function() {
        var list = [{key: "wallie", label: "findwaldonow"}, {label: "monster"}];
        var search = "waldo";
        var result = service.getMatchingOptions(list, search);
        expect(result).toEqual([{key: 'wallie', label: ['find', 'waldo', 'now']}]);
      });
    });

    describe("getFacetChoicesFromFacetsParam", function() {

      it("returns any object passed if not a string", function() {
        expect(service.getFacetChoicesFromFacetsParam({my: "thing"})).toEqual({my: "thing"});
      });

      it("processes a basic JSON string", function() {
        expect(service.getFacetChoicesFromFacetsParam('{"my": "thing"}')).toEqual({my: "thing"});
      });

      it("processes a JSON strings, translating characters", function() {
        expect(service.getFacetChoicesFromFacetsParam('{"my": "\\\\thing\'s"}'))
          .toEqual({my: "\\thing's"});
      });
    });

    describe("getSearchTermsFromQueryString", function() {

      it("returns split of values if no leading question mark", function() {
        var input = "this&is&amazing";
        expect(service.getSearchTermsFromQueryString(input)).toEqual(['this', 'is', 'amazing']);
      });

      it("returns split of values if leading question mark", function() {
        var input = "?this&is&amazing";
        expect(service.getSearchTermsFromQueryString(input)).toEqual(['this', 'is', 'amazing']);
      });
    });

    describe("getName", function() {
      it("extracts the name", function() {
        expect(service.getName({name: 'Joe'})).toEqual('Joe');
      });
    });

    describe("getFacetsFromSearchTerms", function() {
      var types, searchTerm;

      beforeEach(function() {
        types = [{name: 'a', label: 'Apple'}, {name: 'b'}, {name: 'c'}];
      });

      it("returns nothing if given nothing", function() {
        expect(service.getFacetsFromSearchTerms([], searchTerm, 'txt', types)).toEqual([]);
      });

      it("returns nothing if nothing matching", function() {
        var input = ["z=zebra"];
        expect(service.getFacetsFromSearchTerms(input, searchTerm, 'txt', types)).toEqual([]);
      });

      it("returns proper facet if given a match", function() {
        var input = ["a=apple"];
        expect(service.getFacetsFromSearchTerms(input, searchTerm, 'txt', types))
          .toEqual([{name: 'a=apple', label:['Apple','apple']}]);
      });

      it("returns proper facet if given a match with options", function() {
        var input = ["a=gala"];
        types[0].options = [{key: 'gala', label: 'Gala'},{key: 'honeycrisp', label: 'Honeycrisp'}];
        expect(service.getFacetsFromSearchTerms(input, searchTerm, 'txt', types))
          .toEqual([{name: 'a=gala', label:['Apple','Gala']}]);
      });

      it("appends textSearch facet if given a match and a textSearch", function() {
        var input = ["a=apple"];
        searchTerm = 'searchme';
        expect(service.getFacetsFromSearchTerms(input, searchTerm, 'txt', types))
          .toEqual([{name: 'a=apple', label:['Apple','apple']},
            {name: 'text=searchme', label: ['txt', 'searchme']}]);
      });
    });

    describe("getMatchingFacets", function() {

      it("filters properly", function() {
        var list = [{name: "wallie", label: "findwaldonow", options: []}, {label: "monster"}];
        var search = "waldo";
        var result = service.getMatchingFacets(list, search);
        expect(result).toEqual([{name: 'wallie', label: ['find', 'waldo', 'now'], options: []}]);
      });
    });

    describe("removeChoice", function() {

      it("deletes the singletons", function() {
        var facet = {name: "deleteme", singleton: true, options: []};
        var src = [facet, {name: "ok"}];
        var target = [facet, {name: "can't get me"}];
        var name = {type: "deleteme", value: {}};
        service.removeChoice(name, src, target);
        expect(target).toEqual([{name: "can't get me"}]);
      });

      it("deletes the non-singletons", function() {
        var facet = {name: "deleteme", singleton: false, options: []};
        var src = [facet];
        var target = [facet];
        var name = {type: "deleteme", value: {}};
        service.removeChoice(name, src, target);
        expect(target).toEqual([]);
      });

    });

    describe('removeOptionChoice', function() {

      it("removes nothing if no matches", function() {
        var facets = [{name: 'one', options: [{}]}, {name: 'two'}];
        var facetParts = ['nomatch', {}];
        service.removeOptionChoice(facetParts, facets);
        expect(facets).toEqual([{name: 'one', options: [{}]}, {name: 'two'}]);
      });

      it("removes nothing if matches but no options", function() {
        var facets = [{name: 'one', options: [{}]}, {name: 'two'}];
        var facetParts = ['two', {}];
        service.removeOptionChoice(facetParts, facets);
        expect(facets).toEqual([{name: 'one', options: [{}]}, {name: 'two'}]);
      });

      it("removes item if matches and has empty options", function() {
        var facets = [{name: 'one', options: []}, {name: 'two'}];
        var remove = {type: 'one', value: {}};
        service.removeOptionChoice(remove, facets);
        expect(facets).toEqual([{name: 'two'}]);
      });

      it("removes option if key matches but doesn't remove item if options remain", function() {
        var facets = [{name: 'one', options: [{key: 'keymatch'},
          {key: 'notmatch'},{key: 'another'}]}, {name: 'two'}];
        var remove = {type: 'one', value: 'keymatch'};
        service.removeOptionChoice(remove, facets);
        expect(facets).toEqual([{name: 'one',
          options: [{key: 'notmatch'}, {key: 'another'}]}, {name: 'two'}]);
      });

      it("removes all options if key matches", function() {
        var facets = [{name: 'one', options: [{key: 'keymatch'},
          {key: 'keymatch'},{key: 'another'}]}, {name: 'two'}];
        var remove = {type: 'one', value: 'keymatch'};
        service.removeOptionChoice(remove, facets);
        expect(facets).toEqual([{name: 'one', options: [{key: 'another'}]}, {name: 'two'}]);
      });

      it("removes all facets if name matches", function() {
        var facets = [{name: 'one', options: []}, {name: 'one', options: []}, {name: 'two'}];
        var remove = {type: 'one', value: {}};
        service.removeOptionChoice(remove, facets);
        expect(facets).toEqual([{name: 'two'}]);
      });

      it("does nothing if no options defined for a facet", function() {
        var facets = [{name: 'one', options: []}, {name: 'one'}, {name: 'two'}];
        var remove = {type: 'one', value: {}};
        service.removeOptionChoice(remove, facets);
        expect(facets).toEqual([{name: 'one'}, {name: 'two'}]);
      });
    });

    describe("getUnusedFacetChoices", function() {

      it("does nothing with unmatched facet name", function() {
        var facets = ["one=thing", "two=thing"];
        var choices = [{name: "something"}];
        var unused = service.getUnusedFacetChoices(choices, facets);
        expect(unused).toEqual([{name: "something"}]);
      });

      it("removes facet with matched facet name and no options", function() {
        var facets = ["something=thing", "two=thing"];
        var choices = [{name: "something"}];
        var unused = service.getUnusedFacetChoices(choices, facets);
        expect(unused).toEqual([]);
      });

      it("removes facet with matched facet name and options", function() {
        var facets = ["something=thing", "two=thing"];
        var choices = [{name: "something", options: [{key: 'thing'}]},
          {name: "something", options: [{key: 'other'}]},{name: "other"}];
        var unused = service.getUnusedFacetChoices(choices, facets);
        expect(unused).toEqual([ {name: "something", options: [{key: 'other'}]},
          {name: "other"}]);
      });

      it("removes option with matched facet name and options", function() {
        var facets = ["something=thing", "two=thing"];
        var choices = [{name: "something", options: [{key: 'thing'}, {key: 'other'}]},
          {name: "something", options: [{key: 'other'}]},{name: "other"}];
        var unused = service.getUnusedFacetChoices(choices, facets);
        expect(unused).toEqual([ {name: "something", options: [{key: 'other'}]},
          {name: "something", options: [{key: 'other'}]}, {name: "other"}]);
      });

      it("removes facet with matched facet name and options if a singleton", function() {
        var facets = ["something=thing", "another=thing"];
        var choices = [{name: "something", singleton: true,
          options: [{key: 'thing'}, {key: 'other'}]},
          {name: "another", options: [{key: 'thing'}, {key: 'more'}]},{name: "other"}];
        var unused = service.getUnusedFacetChoices(choices, facets);
        expect(unused).toEqual([ {name: "another", options: [{key: 'more'}]},
          {name: "other"}]);
      });
    });
  });
})();
