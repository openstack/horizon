horizon.datatables.set_table_sorting = function (parent) {
  // Function to initialize the tablesorter plugin strictly on sortable columns.
  $(parent).find("table.table").each(function () {
    var $this = $(this),
        options = {};
    $this.find("thead th").each(function (i, val) {
      // Disable if not sortable or has <= 1 item
      if (!$(this).hasClass('sortable') ||
          $this.find('tbody tr').not('.empty').length <= 1) {
        options[i] = {sorter: false};
      }
    });
    $this.tablesorter({
      headers: options
    });
  });
};

horizon.datatables.add_table_checkboxes = function(parent) {
  $(parent).find('table thead .multi_select_column').each(function(index, thead) {
    if (!$(thead).find(':checkbox').length &&
        $(thead).parents('table').find('tbody :checkbox').length) {
      $(thead).append('<input type="checkbox">');
    }
  });
};

horizon.addInitFunction(function() {
  $('div.table_wrapper, div.modal_wrapper').on('click', 'table thead .multi_select_column :checkbox', function(evt) {
    var $this = $(this),
        $table = $this.closest('table'),
        is_checked = $this.prop('checked'),
        checkboxes = $table.find('tbody :checkbox');
    checkboxes.prop('checked', is_checked);
  });
  $('.table_search input').quicksearch('tbody tr', {
    'delay': 300,
    'loader': 'span.loading',
    'bind': 'keyup click',
    'show': function () {
      this.style.display = '';
    },
    'hide': function () {
      this.style.display = 'none';
    },
    'prepareQuery': function (val) {
      return new RegExp(val, "i");
    },
    'testQuery': function (query, txt, _row) {
      return query.test($(_row).find('td:not(.hidden)').text());
    }
  });

  horizon.datatables.add_table_checkboxes($('body'));
  horizon.datatables.set_table_sorting($('body'));

  // Also apply on tables in modal views
  $('div.modal_wrapper').on('shown', '.modal', function(evt) {
    horizon.datatables.add_table_checkboxes(this);
    horizon.datatables.set_table_sorting(this);
  });

  horizon.datatables.update();
});
