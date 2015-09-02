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

});
