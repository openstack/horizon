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

  describe("decode", function() {

    it("Returns value when key is present", inject(function(decodeFilter) {
      expect(decodeFilter('PRESENT', {'PRESENT': 'Here'})).toBe('Here');
    }));

    it("Returns value when key is present and value is falsy", inject(function(decodeFilter) {
      expect(decodeFilter('PRESENT', {'PRESENT': false})).toBe(false);
    }));

    it("Returns input when key is not present", inject(function(decodeFilter) {
      expect(decodeFilter('NOT_PRESENT', {'PRESENT': 'Here'})).toBe('NOT_PRESENT');
    }));

  });

  describe('bytes', function() {

    it('returns TB values', inject(function(bytesFilter) {
      expect(bytesFilter(1099511627776)).toBe('1.00 TB');
    }));

    it('returns GB values', inject(function(bytesFilter) {
      expect(bytesFilter(1073741824)).toBe('1.00 GB');
    }));

    it('returns MB values', inject(function(bytesFilter) {
      expect(bytesFilter(1048576)).toBe('1.00 MB');
    }));

    it('returns KB values', inject(function(bytesFilter) {
      expect(bytesFilter(1024)).toBe('1.00 KB');
    }));

    it('returns byte values', inject(function(bytesFilter) {
      expect(bytesFilter(0)).toBe('0 bytes');
      expect(bytesFilter(1)).toBe('1 bytes');
      expect(bytesFilter(1023)).toBe('1023 bytes');
    }));

  });

  describe('itemCount', function() {

    it('should return translated text with item count',
      inject(function(itemCountFilter) {
        expect(itemCountFilter(null)).toBe('Displaying 0 items');
        expect(itemCountFilter(undefined)).toBe('Displaying 0 items');
        expect(itemCountFilter(true)).toBe('Displaying 1 item');
        expect(itemCountFilter(false)).toBe('Displaying 0 items');
        expect(itemCountFilter('a')).toBe('Displaying 0 items');
        expect(itemCountFilter('0')).toBe('Displaying 0 items');
        expect(itemCountFilter('1')).toBe('Displaying 1 item');
        expect(itemCountFilter('1e1')).toBe('Displaying 10 items');
        expect(itemCountFilter('1b1')).toBe('Displaying 0 items');
        expect(itemCountFilter(0)).toBe('Displaying 0 items');
        expect(itemCountFilter(1)).toBe('Displaying 1 item');
        expect(itemCountFilter(1.2)).toBe('Displaying 1 item');
        expect(itemCountFilter(1.6)).toBe('Displaying 2 items');
        expect(itemCountFilter(-1)).toBe('Displaying 0 items');
        expect(itemCountFilter(-1.2)).toBe('Displaying 0 items');
      })
    );

  });

});
