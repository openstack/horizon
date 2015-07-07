describe("Tables (horizon.tables.js)", function () {

  describe("can hide or reveal column,", function () {
    var fixture, table;
    beforeEach(function () {
      fixture = $("#jasmine-fixture");
      table = fixture.find("#table2");
    });

    it("with a default behaviour.", function () {
      expect(table.find(".cat").is(":hidden")).toBe(false);
      expect(table.find(":not(.cat)").is(":hidden")).toBe(true);
    });

    it("by activating a filter.", function () {
      $("#button_dogs").trigger("click");
      expect(table.find(".dog").is(":hidden")).toBe(false);
      expect(table.find(":not(.dog)").is(":hidden")).toBe(true);

      $("#button_big").trigger("click");
      expect(table.find(".big").is(":hidden")).toBe(false);
      expect(table.find(":not(.big)").is(":hidden")).toBe(true);

      $("#button_cats").trigger("click");
      expect(table.find(".cat").is(":hidden")).toBe(false);
      expect(table.find(":not(.cat)").is(":hidden")).toBe(true);
    });
  });

  describe("can provide a footer counter,", function () {
    var table, tbody, table_count, rows;

    beforeEach(function () {
      table = $("#table1");
      tbody = table.find('tbody');
      table_count = table.find("span.table_count");
      rows = tbody.find('tr');
    });

    it("which count the number of items.", function () {
      horizon.datatables.update_footer_count(table);
      expect(table_count.text()).toContain('4 items');
    });

    it("which can be updated", function () {
      rows.first().hide();
      rows.first().next().hide();
      horizon.datatables.update_footer_count(table);
      expect(table_count.text()).toContain('2 items');

      rows.first().next().show();
      horizon.datatables.update_footer_count(table);
      expect(table_count.text()).toContain('3 items');

      $('<tr><td>cat3</td></tr>"').appendTo(tbody);
      $('<tr><td>cat4</td></tr>"').appendTo(tbody);
      horizon.datatables.update_footer_count(table);
      expect(table_count.text()).toContain('5 items');
    });
  });

  describe("Formset rows:", function () {
     var html, table, input, row, empty_row_html, x;

     beforeEach(function () {
       html = $('#formset');
       table = html.find('table');
       row = table.find('tbody tr').first();
     });

     it("reenumerate", function () {
       input = table.find('tbody tr#flavors__row__14 input').first();
       input.attr('id', 'id_flavors-3-name');
       horizon.formset_table.reenumerate_rows(table, 'flavors');
       expect(input.attr('id')).toEqual('id_flavors-0-name');
       input.attr('id', 'id_flavors-__prefix__-name');
       horizon.formset_table.reenumerate_rows(table, 'flavors');
       expect(input.attr('id')).toEqual('id_flavors-0-name');
     });

     it("delete", function () {
       input = row.find('input#id_flavors-0-DELETE');
       expect(row.css("display")).toEqual('table-row');
       expect(input.attr('checked')).toEqual(undefined);
       horizon.formset_table.replace_delete(row);
       x = input.next('a');
       horizon.formset_table.delete_row.call(x);
       expect(row.css("display")).toEqual('none');
       expect(input.attr('checked')).toEqual('checked');
     });

     it("add", function () {
       empty_row_html = '<tr><td><input id="id_flavors-__prefix__-name" name="flavors-__prefix__-name"></td></tr>';
       expect(table.find('tbody tr').length).toEqual(3);
       expect(html.find('#id_flavors-TOTAL_FORMS').val()).toEqual("3");
       horizon.formset_table.add_row(table, 'flavors', empty_row_html);
       expect(table.find('tbody tr').length).toEqual(4);
       expect(table.find('tbody tr:last input').attr('id')).toEqual('id_flavors-3-name');
       expect(html.find('#id_flavors-TOTAL_FORMS').val()).toEqual("4");
     });
  });

  describe("Init formset table", function () {
     var html, table;

     beforeEach(function () {
       html = $('#formset');
       table = html.find('table');
     });

     it("add row", function () {
       horizon.formset_table.init('flavors', '', 'Add row');
       expect(table.find('tfoot tr a').html()).toEqual('Add row');
     });

     it("no add row", function () {
       $('tfoot tr a').remove();
       horizon.formset_table.init('flavors', '', '');
       expect(table.find('tfoot tr a').length).toEqual(0);
     });
  });
});