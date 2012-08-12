/* Namespace for core functionality related to DataTables. */
horizon.datatables = {
  update: function () {
    var $rows_to_update = $('tr.status_unknown.ajax-update');
    if ($rows_to_update.length) {
      var interval = $rows_to_update.attr('data-update-interval'),
          $table = $rows_to_update.closest('table'),
          decay_constant = $table.attr('decay_constant');

      // Do not update this row if the action column is expanded
      if ($rows_to_update.find('.actions_column .btn-group.open').length) {
        // Wait and try to update again in next interval instead
        setTimeout(horizon.datatables.update, interval);
        // Remove interval decay, since this will not hit server
        $table.removeAttr('decay_constant');
        return;
      }
      // Trigger the update handlers.
      $rows_to_update.each(function(index, row) {
        var $row = $(this),
            $table = $row.closest('table');
        horizon.ajax.queue({
          url: $row.attr('data-update-url'),
          error: function (jqXHR, textStatus, errorThrown) {
            switch (jqXHR.status) {
              // A 404 indicates the object is gone, and should be removed from the table
              case 404:
                // Update the footer count and reset to default empty row if needed
                var $footer = $table.find('tr:last'),
                    row_count, footer_text, colspan, template, params, $empty_row;

                // existing count minus one for the row we're removing
                row_count = $table.find('tbody tr').length - 1;
                footer_text = "Displaying " + row_count + " item";
                if(row_count !== 1) {
                    footer_text += 's';
                }
                $footer.find('span').text(footer_text);

                if(row_count === 0) {
                  colspan = $footer.find('td').attr('colspan');
                  template = horizon.templates.compiled_templates["#empty_row_template"];
                  params = {"colspan": colspan};
                  empty_row = template.render(params);
                  $row.replaceWith(empty_row);
                } else {
                  $row.remove();
                }
                break;
              default:
                if (horizon.conf.debug) {
                  horizon.alert("error", gettext("An error occurred while updating."));
                }
                $row.removeClass("ajax-update");
                $row.find("i.ajax-updating").remove();
                break;
            }
          },
          success: function (data, textStatus, jqXHR) {
            var $new_row = $(data);

            if($new_row.hasClass('status_unknown')) {
              var spinner_elm = $new_row.find("td.status_unknown:last");
              // Replacing spin.js here with an animated gif to reduce CPU
              spinner_elm.prepend(
                      $("<div />")
                      .addClass("loading_gif")
                      .append(
                          $("<img />")
                          .attr("src", "/static/dashboard/img/loading.gif")));
            }

            // Only replace row if the html content has changed
            if($new_row.html() != $row.html()) {
              if($row.find(':checkbox').is(':checked')) {
                // Preserve the checkbox if it's already clicked
                $new_row.find(':checkbox').prop('checked', true);
              }
              $row.replaceWith($new_row);
              // Reset decay constant.
              $table.removeAttr('decay_constant');
            }
          },
          complete: function (jqXHR, textStatus) {
            // Revalidate the button check for the updated table
            horizon.datatables.validate_button();
          }
        });
      });

      // Set interval decay to this table, and increase if it already exist
      if(decay_constant === undefined) {
        decay_constant = 1;
      } else {
        decay_constant++;
      }
      $table.attr('decay_constant', decay_constant);
      // Poll until there are no rows in an "unknown" state on the page.
      next_poll = interval * decay_constant;
      // Limit the interval to 30 secs
      if(next_poll > 30 * 1000) next_poll = 30 * 1000;
      setTimeout(horizon.datatables.update, next_poll);
    }
  },

  validate_button: function () {
    // Disable form button if checkbox are not checked
    $("form").each(function (i) {
      var checkboxes = $(this).find(":checkbox");
      if(!checkboxes.length) {
        // Do nothing if no checkboxes in this form
        return;
      }
      if(!checkboxes.filter(":checked").length) {
        $(this).find(".table_actions button.btn-danger").addClass("disabled");
      }
    });
  }
};

/* Generates a confirmation modal dialog for the given action. */
horizon.datatables.confirm = function (action) {
  var $action = $(action),
      $modal_parent = $(action).closest('.modal'),
      action_string, title, body, modal, form;
  if($action.hasClass("disabled")) {
    return;
  }
  action_string = $action.text();
  title = gettext("Confirm ") + action_string;
  body = gettext("Please confirm your selection. This action cannot be undone.");
  modal = horizon.modals.create(title, body, action_string);
  modal.modal();
  if($modal_parent.length) {
    var child_backdrop = modal.next('.modal-backdrop');
    // re-arrange z-index for these stacking modal
    child_backdrop.css('z-index', $modal_parent.css('z-index')+10);
    modal.css('z-index', child_backdrop.css('z-index')+10);
  }
  modal.find('.btn-primary').click(function (evt) {
    form = $action.closest('form');
    form.append("<input type='hidden' name='" + $action.attr('name') + "' value='" + $action.attr('value') + "'/>");
    form.submit();
    modal.modal('hide');
    horizon.modals.modal_spinner(gettext("Working"));
    return false;
  });
  return modal;
};

$.tablesorter.addParser({
    // set a unique id
    id: 'sizeSorter',
    is: function(s) {
        // Not an auto-detected parser
        return false;
    },
    // compare int values
    format: function(s) {
      var sizes = {BYTE: 0, B: 0, KB: 1, MB: 2,
                   GB: 3, TB: 4, PB: 5};
      var regex = /([\d\.,]+)\s*(byte|B|KB|MB|GB|TB|PB)+/i;
      var match = s.match(regex);
      if (match && match.length === 3){
        return parseFloat(match[1]) *
                          Math.pow(1024, sizes[match[2].toUpperCase()]);
      }
      return parseInt(s, 10);
    },
    type: 'numeric'
});

horizon.datatables.set_table_sorting = function (parent) {
// Function to initialize the tablesorter plugin strictly on sortable columns.
$(parent).find("table.table").each(function () {
  var $table = $(this),
      header_options = {};
  // Disable if not sortable or has <= 1 item
  if ($table.find('tbody tr').not('.empty').length > 1){
    $table.find("thead th").each(function (i, val) {
      $th = $(this);
      if (!$th.hasClass('sortable')) {
        header_options[i] = {sorter: false};
      } else if ($th.data('type') == 'size'){
        // set as [i-1] as there is one more <th> in <thead>
        // than <td>'s in <tbody>
        header_options[i-1] = {sorter: 'sizeSorter'};
      }
    });
    $table.tablesorter({
      headers: header_options,
      cancelSelection: false
    });
  }
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

horizon.datatables.set_table_filter = function (parent) {
  $(parent).find('table').each(function (index, elm) {
    var input = $($(elm).find('div.table_search input'));
    if (input) {
      input.quicksearch('table#' + $(elm).attr('id') + ' tbody tr', {
        'delay': 300,
        'loader': 'span.loading',
        'bind': 'keyup click',
        'show': this.show,
        'hide': this.hide,
        'prepareQuery': function (val) {
          return new RegExp(val, "i");
        },
        'testQuery': function (query, txt, _row) {
          return query.test($(_row).find('td:not(.hidden)').text());
        }
      });
    }
  });
};

horizon.addInitFunction(function() {
  horizon.datatables.validate_button();

  // Bind the "select all" checkbox action.
  $('div.table_wrapper, #modal_wrapper').on('click', 'table thead .multi_select_column :checkbox', function(evt) {
    var $this = $(this),
        $table = $this.closest('table'),
        is_checked = $this.prop('checked'),
        checkboxes = $table.find('tbody :checkbox');
    checkboxes.prop('checked', is_checked);
  });

  // Enable dangerous buttons only if one or more checkbox is checked.
  $("div.table_wrapper, #modal_wrapper").on("click", ':checkbox', function (evt) {
    var $form = $(this).closest("form");
    var any_checked = $form.find("tbody :checkbox").is(":checked");
    if(any_checked) {
      $form.find(".table_actions button.btn-danger").removeClass("disabled");
    }else {
      $form.find(".table_actions button.btn-danger").addClass("disabled");
    }
  });

  // Trigger run-once setup scripts for tables.
  horizon.datatables.add_table_checkboxes($('body'));
  horizon.datatables.set_table_sorting($('body'));
  horizon.datatables.set_table_filter($('body'));

  // Also apply on tables in modal views.
  horizon.modals.addModalInitFunction(horizon.datatables.add_table_checkboxes);
  horizon.modals.addModalInitFunction(horizon.datatables.set_table_sorting);
  horizon.modals.addModalInitFunction(horizon.datatables.set_table_filter);

  horizon.datatables.update();
});
