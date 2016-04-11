(function () {
  'use strict';

  describe('horizon.framework.util.extensible module', function () {
    it('should have been defined', function () {
      expect(angular.module('horizon.framework.util.extensible')).toBeDefined();
    });
  });

  describe('extensible service', function () {
    var extensibleService, container, items;

    beforeEach(module('horizon.framework.util.extensible'));

    beforeEach(inject(function ($injector) {
      extensibleService = $injector.get('horizon.framework.util.extensible.service');
      container = {};
      items = [ { id: '1' }, { id: '2' }, { id: '3' } ];
      extensibleService(container, items);
    }));

    it('can append items', function () {
      expect(items.length).toBe(3);

      var item4 = { id: '4' };
      container.append(item4, 1);
      expect(items.length).toBe(4);
      expect(items[3]).toBe(item4);

      var item5 = { id: '5' };
      container.append(item5);
      expect(items.length).toBe(5);
      expect(items[3]).toBe(item5);
      expect(items[4]).toBe(item4);

      var item6 = { id: '6' };
      container.append(item6, 2);
      expect(items.length).toBe(6);
      expect(items[3]).toBe(item5);
      expect(items[4]).toBe(item6);
      expect(items[5]).toBe(item4);

      var item7 = { id: '7' };
      container.append(item7, 1);
      expect(items.length).toBe(7);
      expect(items[3]).toBe(item5);
      expect(items[4]).toBe(item6);
      expect(items[5]).toBe(item4);
      expect(items[6]).toBe(item7);

      var item8 = { id: '8' };
      container.append(item8);
      expect(items.length).toBe(8);
      expect(items[3]).toBe(item5);
      expect(items[4]).toBe(item8);
      expect(items[5]).toBe(item6);
      expect(items[6]).toBe(item4);
      expect(items[7]).toBe(item7);
    });

    it('can prepend items', function () {
      expect(items.length).toBe(3);

      var item4 = { id: '4' };
      container.prepend(item4, 1);
      expect(items.length).toBe(4);
      expect(items[0]).toBe(item4);

      var item5 = { id: '5' };
      container.prepend(item5);
      expect(items.length).toBe(5);
      expect(items[0]).toBe(item4);
      expect(items[1]).toBe(item5);

      var item6 = { id: '6' };
      container.prepend(item6, 2);
      expect(items.length).toBe(6);
      expect(items[0]).toBe(item4);
      expect(items[1]).toBe(item6);
      expect(items[2]).toBe(item5);

      var item7 = { id: '7' };
      container.prepend(item7, 1);
      expect(items.length).toBe(7);
      expect(items[0]).toBe(item7);
      expect(items[1]).toBe(item4);
      expect(items[2]).toBe(item6);
      expect(items[3]).toBe(item5);

      var item8 = { id: '8' };
      container.prepend(item8);
      expect(items.length).toBe(8);
      expect(items[0]).toBe(item7);
      expect(items[1]).toBe(item4);
      expect(items[2]).toBe(item6);
      expect(items[3]).toBe(item8);
      expect(items[4]).toBe(item5);
    });

    it('can insert items', function () {
      expect(items.length).toBe(3);

      var item4 = { id: '4' };
      container.after('1', item4, 1);
      expect(items.length).toBe(4);
      expect(items[1]).toBe(item4);

      var item5 = { id: '5' };
      container.after('1', item5);
      expect(items.length).toBe(5);
      expect(items[1]).toBe(item4);
      expect(items[2]).toBe(item5);

      var item6 = { id: '6' };
      container.after('1', item6, 2);
      expect(items.length).toBe(6);
      expect(items[1]).toBe(item4);
      expect(items[2]).toBe(item6);
      expect(items[3]).toBe(item5);

      var item7 = { id: '7' };
      container.after('1', item7, 1);
      expect(items.length).toBe(7);
      expect(items[1]).toBe(item7);
      expect(items[2]).toBe(item4);
      expect(items[3]).toBe(item6);
      expect(items[4]).toBe(item5);

      var item8 = { id: '8' };
      container.after('1', item8);
      expect(items.length).toBe(8);
      expect(items[1]).toBe(item7);
      expect(items[2]).toBe(item4);
      expect(items[3]).toBe(item6);
      expect(items[4]).toBe(item8);
      expect(items[5]).toBe(item5);

      var last = { id: 'last' };
      container.after('3', last);
      expect(items.length).toBe(9);
      expect(items[8]).toBe(last);

      var insert = function() {
        container.after('foo', { id: 'bar' });
      };
      expect(insert).toThrowError(Error, 'Item with id foo not found.');
    });

    it('can remove items', function () {
      expect(items.length).toBe(3);
      container.remove('2');
      expect(items.length).toBe(2);
      container.remove('1');
      expect(items.length).toBe(1);

      var remove = function() {
        container.remove('foo');
      };
      expect(remove).toThrowError(Error, 'Item with id foo not found.');
    });

    it('can replace items', function () {
      expect(items.length).toBe(3);

      var item4 = { id: '4' };
      container.replace('2', item4);
      expect(items.length).toBe(3);
      expect(items[1]).toBe(item4);

      var item5 = { id: '5' };
      container.replace('1', item5);
      expect(items.length).toBe(3);
      expect(items[0]).toBe(item5);
      expect(items[1]).toBe(item4);
      expect(items[2].id).toBe('3');

      var replace = function() {
        container.replace('foo', { id: 'bar' });
      };
      expect(replace).toThrowError(Error, 'Item with id foo not found.');
    });

    it('can add controllers', function () {
      expect(container.controllers.length).toBe(0);
      container.addController('MyController');
      expect(container.controllers.length).toBe(1);
    });

    it('can chain method calls', function () {
      container
        .append({ id: '4' })
        .prepend({ id: '5' })
        .after('1', { id: '6' })
        .remove('3')
        .replace('2', { id: '7' })
        .addController('foo');
      expect(items.map(function getId(item) {
        return item.id;
      })).toEqual(['5', '1', '6', '7', '4']);
    });
  });

})();
