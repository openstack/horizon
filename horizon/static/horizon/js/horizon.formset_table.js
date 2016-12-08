/**
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

horizon.formset_table = (function () {
  'use strict';

  var module = {};


  // go through the whole table and fix the numbering of rows
  module.reenumerate_rows = function (table, prefix) {
    var count = 0;
    var input_name_re = new RegExp('^' + prefix + '-(\\d+|__prefix__)-');
    var input_id_re = new RegExp('^id_' + prefix + '-(\\d+|__prefix__)-');

    table.find('tbody tr').each(function () {
      $(this).find('input').each(function () {
        var input = $(this);
        input.attr('name', input.attr('name').replace(
          input_name_re, prefix + '-' + count + '-'));
        input.attr('id', input.attr('id').replace(
          input_id_re, 'id_' + prefix + '-' + count + '-'));
      });
      count += 1;
    });
    $('#id_' + prefix + '-TOTAL_FORMS').val(count);
  };

  // mark a row as deleted and hide it
  module.delete_row = function () {
    $(this).closest('tr').hide();
    $(this).prev('input[name$="-DELETE"]').attr('checked', true);
  };

  // replace the "Delete" checkboxes with × for deleting rows
  module.replace_delete = function (where) {
    where.find('input[name$="-DELETE"]').hide().after(
      $('<a href="#" class="close">×</a>').click(module.delete_row)
    );
  };

  // add more empty rows in the flavors table
  module.add_row = function (table, prefix, empty_row_html) {
    var new_row = $(empty_row_html);
    module.replace_delete(new_row);
    table.find('tbody').append(new_row);
    module.reenumerate_rows(table, prefix);
  };

  // prepare all the javascript for formset table
  module.init = function (prefix, empty_row_html, add_label) {

    var table = $('table#' + prefix);

    module.replace_delete(table);

    // if there are extra empty rows, add the button for new rows
    if (add_label) {
      var button = $('<a href="#" class="btn btn-primary btn-sm pull-right">' +
        add_label + '</a>');
      table.find('tfoot td').append(button);
      button.click(function () {
        module.add_row(table, prefix, empty_row_html);
      });
    }

    // if the formset is not empty and has no errors,
    // delete the empty extra rows from the end
    var initial_forms = +$('#id_' + prefix + '-INITIAL_FORMS').val();
    var total_forms = +$('#id_' + prefix + '-TOTAL_FORMS').val();

    if (table.find('tbody tr').length > 1 &&
      table.find('tbody td.error').length === 0 &&
      total_forms > initial_forms) {
      table.find('tbody tr').each(function (index) {
        if (index >= initial_forms) {
          $(this).remove();
        }
      });
      module.reenumerate_rows(table, prefix);
      $('#id_' + prefix + '-INITIAL_FORMS').val(
        $('#id_' + prefix + '-TOTAL_FORMS').val());
    }

    // enable tooltips
    table.find('td.error[title]').tooltip();
  };

  return module;
} ());
