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

/* Core functionality related to extensible header sections. */
horizon.extensible_header = {
  populate: function() {
    var $path = $(location).attr('pathname');
    var $url = $(location).attr('href');
    $url = $url.replace($path, $(window).attr('WEBROOT') + 'header/');

    horizon.ajax.queue({
      url: $url,
      success: function(data) {
        $('#extensible-header').replaceWith($(data));

        selected = horizon.cookies.get('selected_header');
        if(selected && $('#header-list #' + selected).length){
          $old_primary = $('#primary-extensible-header > a');
          $new_primary = $('#header-list #' + selected);

          $old_primary.insertAfter($new_primary);
          $new_primary.first().appendTo($('#primary-extensible-header'));
        }

        function swap() {
          $old_primary = $('#primary-extensible-header > a');
          $new_primary = $(this);

          horizon.cookies.put("selected_header", $new_primary.attr('id'), {path:'/'});
          $old_primary.insertAfter($new_primary);
          $new_primary.appendTo($('#primary-extensible-header'));
          $new_primary.off('click', swap);
          $old_primary.on('click', swap);
        }
        $('#header-list .extensible-header-section').on('click', swap);
      },
      error: function(jqXHR) {
        if (jqXHR.status !== 401 && jqXHR.status !== 403) {
          // error is raised with status of 0 when ajax query is cancelled
          // due to new page request
          if (jqXHR.status !== 0) {
            horizon.alert("info", gettext("Failed to populate extensible header."));
          }
        }
      }
    });
    return true;
  }
};

horizon.addInitFunction(function() {
  // trigger extensible header section query on page load
  horizon.extensible_header.populate();
});
