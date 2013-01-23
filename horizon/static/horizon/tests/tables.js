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
    var table =  fixture.find("#table1");
    var tbody = table.find('tbody');
    var table_count = table.find("span.table_count");
    var rows = tbody.find('tr');

    horizon.datatables.update_footer_count(table);
    notEqual(table_count.text().indexOf('4 items'), -1, "Initial count is correct");

    // hide rows
    rows.first().hide();
    rows.first().next().hide();
    horizon.datatables.update_footer_count(table);
    notEqual(table_count.text().indexOf('2 items'), -1, "Count correct after hiding two rows");

    // show a row
    rows.first().next().show();
    horizon.datatables.update_footer_count(table);
    notEqual(table_count.text().indexOf('3 items'), -1, "Count correct after showing one row");

    // add rows
    $('<tr><td>cat3</td></tr>"').appendTo(tbody);
    $('<tr><td>cat4</td></tr>"').appendTo(tbody);
    horizon.datatables.update_footer_count(table);
    notEqual(table_count.text().indexOf('5 items'), -1, "Count correct after adding two rows");
});
