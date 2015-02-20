describe('hz.filters', function () {
  'use strict';

   beforeEach(module('hz.filters'));

   describe('yesno', function() {

     it('returns Yes for true', inject(function(yesnoFilter) {
       expect(yesnoFilter(true)).toBe('Yes');
     }));

     it('returns No for false', inject(function(yesnoFilter) {
       expect(yesnoFilter(false)).toBe('No');
     }));

     it('returns No for null', inject(function(yesnoFilter) {
       expect(yesnoFilter(null)).toBe('No');
     }));

   });

   describe('gb', function() {

     it('returns given numeric value properly', inject(function(gbFilter) {
       expect(gbFilter(12)).toBe('12 GB');
       expect(gbFilter(-12)).toBe('-12 GB');
       expect(gbFilter(12.12)).toBe('12.12 GB');
     }));

     it('returns empty string for non-numeric', inject(function(gbFilter) {
       expect(gbFilter('humbug')).toBe('');
     }));

     it('returns empty string for null', inject(function(gbFilter) {
       expect(gbFilter(null)).toBe('');
     }));

   });

   describe('mb', function() {

     it('returns given numeric value properly', inject(function(mbFilter) {
       expect(mbFilter(12)).toBe('12 MB');
       expect(mbFilter(-12)).toBe('-12 MB');
       expect(mbFilter(12.12)).toBe('12.12 MB');
     }));

     it('returns empty string for non-numeric', inject(function(mbFilter) {
       expect(mbFilter('humbug')).toBe('');
     }));

     it('returns empty string for null', inject(function(mbFilter) {
       expect(mbFilter(null)).toBe('');
     }));

   });

  describe('title', function() {

    it('capitalizes as expected', inject(function(titleFilter) {
      expect(titleFilter('title')).toBe('Title');
      expect(titleFilter('we have several words')).toBe('We Have Several Words');
    }));

  });

  describe('noUnderscore', function() {

    it('replaces all underscores with spaces', inject(function(noUnderscoreFilter) {
      expect(noUnderscoreFilter('_this_is___a_lot____of_underscores__')).toBe(' this is   a lot    of underscores  ');
    }));

    it('returns falsy input', inject(function(noUnderscoreFilter) {
      expect(noUnderscoreFilter(null)).toBe(null);
      expect(noUnderscoreFilter(false)).toBe(false);
      expect(noUnderscoreFilter('')).toBe('');
    }));

  });

});
