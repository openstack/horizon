module("Tables (horizon.tables.js)");

test("Row filtering (fixed)", function () {
  var fixture = $("#qunit-fixture");
  var table = fixture.find("#table2");

  ok(!table.find(".cat").is(":hidden"), "Filtering cats: cats visible by default");
  ok(table.find(":not(.cat)").is(":hidden"), "Filtering cats: non-cats hidden by default");

  $("#button_cats").trigger("click");
  ok(!table.find(".cat").is(":hidden"), "Filtering cats: cats visible");
  ok(table.find(":not(.cat)").is(":hidden"), "Filtering cats: non-cats hidden");

  $("#button_dogs").trigger("click");
  ok(!table.find(".dog").is(":hidden"), "Filtering dogs: dogs visible");
  ok(table.find(":not(.dog)").is(":hidden"), "Filtering dogs: non-dogs hidden");

  $("#button_big").trigger("click");
  ok(!table.find(".big").is(":hidden"), "Filtering big animals: big visible");
  ok(table.find(":not(.big)").is(":hidden"), "Filtering big animals: non-big hidden");
});

test("Footer count update", function () {
  var fixture = $("#qunit-fixture");
  var table = fixture.find("#table1");
  var tbody = table.find('tbody');
  var table_count = table.find("span.table_count");
  var rows = tbody.find('tr');

  // The following function returns the first set of consecutive numbers.
  // This is allows you to match an inner numeric value regardless of
  // the language and regardless of placement within the phrase.
  // If you want to match '4' for your numeric value, the following are ok:
  // "there are 4 lights", "4 lights there are", "lights there are 4" but
  // not "there are 14 lights".
  var get_consec_nums = function(str) { return (str.match(/\d+/) || [""])[0]; };

  horizon.datatables.update_footer_count(table);
  equal(get_consec_nums(table_count.text()), '4', "Initial count is correct");

  // hide rows
  rows.first().hide();
  rows.first().next().hide();
  horizon.datatables.update_footer_count(table);
  equal(get_consec_nums(table_count.text()), '2', "Count correct after hiding two rows");

  // show a row
  rows.first().next().show();
  horizon.datatables.update_footer_count(table);
  equal(get_consec_nums(table_count.text()), '3', "Count correct after showing one row");

  // add rows
  $('<tr><td>cat3</td></tr>"').appendTo(tbody);
  $('<tr><td>cat4</td></tr>"').appendTo(tbody);
  horizon.datatables.update_footer_count(table);
  equal(get_consec_nums(table_count.text()), '5', "Count correct after adding two rows");
});

test("Formset reenumerate rows", function () {
  var html = $('#formset');
  var table = html.find('table');
  var input = table.find('tbody tr#flavors__row__14 input').first();

  input.attr('id', 'id_flavors-3-name');
  horizon.formset_table.reenumerate_rows(table, 'flavors');
  equal(input.attr('id'), 'id_flavors-0-name', "Enumerate old rows ids");
  input.attr('id', 'id_flavors-__prefix__-name');
  horizon.formset_table.reenumerate_rows(table, 'flavors');
  equal(input.attr('id'), 'id_flavors-0-name', "Enumerate new rows ids");
});

test("Formset delete row", function () {
  var html = $('#formset');
  var table = html.find('table');
  var row = table.find('tbody tr').first();
  var input = row.find('input#id_flavors-0-DELETE');

  equal(row.css("display"), 'table-row');
  equal(input.attr('checked'), undefined);
  horizon.formset_table.replace_delete(row);
  var x = input.next('a');
  horizon.formset_table.delete_row.call(x);
  equal(row.css("display"), 'none');
  equal(input.attr('checked'), 'checked');
});

test("Formset add row", function() {
  var html = $('#formset');
  var table = html.find('table');
  var empty_row_html = '<tr><td><input id="id_flavors-__prefix__-name" name="flavors-__prefix__-name"></td></tr>';

  equal(table.find('tbody tr').length, 3);
  equal(html.find('#id_flavors-TOTAL_FORMS').val(), 3);
  horizon.formset_table.add_row(table, 'flavors', empty_row_html);
  equal(table.find('tbody tr').length, 4);
  equal(table.find('tbody tr:last input').attr('id'), 'id_flavors-3-name');
  equal(html.find('#id_flavors-TOTAL_FORMS').val(), 4);
});

test("Init formset table", function() {
  var html = $('#formset');
  var table = html.find('table');

  horizon.formset_table.init('flavors', '', 'Add row');
  equal(table.find('tfoot tr a').html(), 'Add row');
});

test("Init formset table -- no add", function() {
  var html = $('#formset');
  var table = html.find('table');

  horizon.formset_table.init('flavors', '', '');
  equal(table.find('tfoot tr a').length, 0);
});
