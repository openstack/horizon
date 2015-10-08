describe("Quotas (horizon.quota.js)", function() {

  describe("humanizeNumbers", function() {

    it('should add a comma every three number', function () {
      expect(horizon.Quota.humanizeNumbers('1234')).toEqual('1,234');
      expect(horizon.Quota.humanizeNumbers('1234567')).toEqual('1,234,567');
    });

    it('should work string or numbers', function () {
      expect(horizon.Quota.humanizeNumbers('1234')).toEqual('1,234');
      expect(horizon.Quota.humanizeNumbers(1234)).toEqual('1,234');
    });

    it('should work with multiple values inside a string', function () {
      expect(horizon.Quota.humanizeNumbers('My Total: 1234')).toEqual('My Total: 1,234');

      expect(horizon.Quota.humanizeNumbers('My Total: 1234, His Total: 1234567')).toEqual('My Total: 1,234, His Total: 1,234,567');
    });

  });

  describe("truncate", function() {
    var string = 'This will be cut';
    var ellipsis = '&hellip;';

    it('should truncate a string at a given length', function () {
      expect(horizon.Quota.truncate(string, 15)).toEqual(string.slice(0, 15));
      expect(horizon.Quota.truncate(string, 20)).toEqual(string);
    });

    it('should add an ellipsis if needed ', function () {
      expect(horizon.Quota.truncate(string, 15, true)).toEqual(string.slice(0, 12) + ellipsis);

      expect(horizon.Quota.truncate(string, 20, true)).toEqual(string);

      expect(horizon.Quota.truncate(string, 2, true)).toEqual(ellipsis);
    });
  });

});
