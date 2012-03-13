horizon.addInitFunction(function() {
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

  $('table.sortable').each(function(index, table) {
      var $table = $(table);
      // Only trigger if we have actual data rows in the table.
      // Calling on an empty table throws a javascript error.
      if ($table.find('tbody tr').length) {
        $table.tablesorter();
      }
    });

  $('table').on('click', 'tr .ajax-update', function (evt) {
    var $this = $(this);
    var $table = $this.closest('table');
    $.ajax($this.attr('href'), {
      complete: function (jqXHR, status) {
        var $new_row = $(jqXHR.responseText);
        var $old_row = $this.closest('tr');
        $new_row.find("td.status_unknown").prepend('<i class="icon-updating ajax-updating"></i>');
        // Only replace row if the html content has changed
        if($new_row.html() != $old_row.html()) {
          if($old_row.find(':checkbox').is(':checked')) {
            // Preserve the checkbox if it's already clicked
            $new_row.find(':checkbox').prop('checked', true);
          }
          $old_row.replaceWith($new_row);
          $table.removeAttr('decay_constant');
        }
        // Revalidate the button check for updated table
        horizon.datatables.validate_button();
      }
    });
    return false;
  });

  horizon.datatables.update();
});
