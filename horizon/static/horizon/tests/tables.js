module("Tables (horizon.tables.js)");

test("Footer count update", function () {
    var fixture = $("#qunit-fixture");
    var table =  fixture.find("table.datatable");
    var tbody = table.find('tbody');
    var table_count = table.find("span.table_count");

    horizon.datatables.update_footer_count(table);
    notEqual(table_count.text().indexOf('4 items'), -1, "Initial count is correct");

    // hide rows
    $("table.datatable tbody tr#dog1").hide();
    $("table.datatable tbody tr#cat2").hide();
    horizon.datatables.update_footer_count(table);
    notEqual(table_count.text().indexOf('2 items'), -1, "Count correct after hiding two rows");

    // show a row
    $("table.datatable tbody tr#cat2").show();
    horizon.datatables.update_footer_count(table);
    notEqual(table_count.text().indexOf('3 items'), -1, "Count correct after showing one row");

    // add rows
    $("table.datatable tbody tr#cat2").show();
    $('<tr id="cat3"><td>cat3</td></tr>"').appendTo(tbody);
    $('<tr id="cat4"><td>cat4</td></tr>"').appendTo(tbody);
    horizon.datatables.update_footer_count(table);
    notEqual(table_count.text().indexOf('5 items'), -1, "Count correct after adding two rows");
});
