/* Namespace for core functionality related to Role-Permission Workflow Step.
 * Based on the role step. 
 */
horizon.fiware_roles_workflow = {

  current_relations: [],
  data: [],
  permissions: [],
  //has_permissions: [],
  
  //default_permission_id: [],

  /* Parses the form field selector's ID to get either the
   * role or user id (i.e. returns "id12345" when
   * passed the selector with id: "id_group_id12345").
   **/
  get_field_id: function(id_string) {
    return id_string.slice(id_string.lastIndexOf("_") + 1);
  },

  /*
   * Gets the html select element associated with a given
   * permission id.
   **/
  get_permission_element: function(step_slug, permission_id) {
    return $('select[id^="id_' + step_slug + '_permission_' + permission_id + '"]');
  },

  /*
   * Gets the html ul element associated with a given
   * data id. I.e., the member's row.
   **/
  get_member_element: function(step_slug, data_id) {
    return $('li[data-' + step_slug + '-id$=' + data_id + ']').parent();
  },

  /*
   * Initializes all of the horizon.fiware_roles_workflow lists with
   * data parsed from the hidden form fields, as well as the
   * default permission id.
   **/
  init_properties: function(step_slug) {
    //horizon.fiware_roles_workflow.has_permissions[step_slug] = $("." + step_slug + "_role").data('show-roles') !== "False";
    //horizon.fiware_roles_workflow.default_permission_id[step_slug] = $('#id_default_' + step_slug + '_role').attr('value');
    horizon.fiware_roles_workflow.init_data_list(step_slug);
    horizon.fiware_roles_workflow.init_permission_list(step_slug);
    horizon.fiware_roles_workflow.init_current_relations(step_slug);
  },

  /*
   * Initializes an associative array mapping data ids to display names.
   **/
  init_data_list: function(step_slug) {
    horizon.fiware_roles_workflow.data[step_slug] = [];
    angular.forEach($(this.get_permission_element(step_slug, "")).find("option"), function (option) {
      horizon.fiware_roles_workflow.data[step_slug][option.value] = option.text;
    });
  },

  /*
   * Initializes an associative array mapping permission ids to permission names.
   **/
  init_permission_list: function(step_slug) {
    horizon.fiware_roles_workflow.permissions[step_slug] = [];
    angular.forEach($('label[for^="id_' + step_slug + '_permission_"]'), function(permission) {
      var id = horizon.fiware_roles_workflow.get_field_id($(permission).attr('for'));
      horizon.fiware_roles_workflow.permissions[step_slug][id] = $(permission).text();
    });
  },

  /*
   * Initializes an associative array of lists of the current
   * members for each available permission.
   **/
  init_current_relations: function(step_slug) {
    horizon.fiware_roles_workflow.current_relations[step_slug] = [];
    var roles_list = [];
    var permission_name, permission_id, selected_members;
    angular.forEach(this.get_permission_element(step_slug, ''), function(value, key) {
      permission_id = horizon.fiware_roles_workflow.get_field_id($(value).attr('id'));
      permission_name = $('label[for="id_' + step_slug + '_permission_' + permission_id + '"]').text();

      // get the array of members who are selected in this list
      selected_members = $(value).find("option:selected");
      // extract the member names and add them to the dictionary of lists
      roles_list = [];
      if (selected_members) {
        angular.forEach(selected_members, function(member) {
          roles_list.push(member.value);
        });
      }
      horizon.fiware_roles_workflow.current_relations[step_slug][permission_id] = roles_list;
    });
  },

  /*
   * Returns the ids of permissions the data is role of.
   **/
  get_role_permissions: function(step_slug, data_id) {
    var permissions = [];
    for (var permission in horizon.fiware_roles_workflow.current_relations[step_slug]) {
      if ($.inArray(data_id, horizon.fiware_roles_workflow.current_relations[step_slug][permission]) !== -1) {
        permissions.push(permission);
      }
    }
    return permissions;
  },

  /*
   * Updates the selected values on the permission_list's form field, as
   * well as the current_relations dictionary's list.
   **/
  update_permission_lists: function(step_slug, permission_id, new_list) {
    this.get_permission_element(step_slug, permission_id).val(new_list);
    horizon.fiware_roles_workflow.current_relations[step_slug][permission_id] = new_list;
  },

  /*
   * Helper function for remove_role_from_permission.
   **/
  remove_role: function(step_slug, data_id, permission_id, permission_list) {
    var index = permission_list.indexOf(data_id);
    if (index >= 0) {
      // remove member from list
      permission_list.splice(index, 1);
      horizon.fiware_roles_workflow.update_permission_lists(step_slug, permission_id, permission_list);
    }
  },

  /*
   * Searches through the permission lists and removes a given member
   * from the lists.
   **/
  remove_role_from_permission: function(step_slug, data_id, permission_id) {
    var permission, role = horizon.fiware_roles_workflow.current_relations[step_slug];
    if (permission_id) {
      horizon.fiware_roles_workflow.remove_role(
        step_slug, data_id, permission_id, role[permission_id]
      );
    }
    else {
      // search for role in permission lists
      for (permission in role) {
        if (role.hasOwnProperty(permission)) {
          horizon.fiware_roles_workflow.remove_role(
            step_slug, data_id, permission, role[permission]
          );
        }
      }
    }
  },

  /*
   * Adds a role to a given permission list.
   **/
  add_role_to_permission: function(step_slug, data_id, permission_id) {
    var permission_list = horizon.fiware_roles_workflow.current_relations[step_slug][permission_id];
    permission_list.push(data_id);
    horizon.fiware_roles_workflow.update_permission_lists(step_slug, permission_id, permission_list);
  },

  update_role_permission_list: function(step_slug, data_id) {
    //if (typeof(permission_ids) === 'undefined') {
    permission_ids = horizon.fiware_roles_workflow.get_role_permissions(step_slug, data_id);
    //}
    /*if (typeof(role_el) === 'undefined') {
      role_el = horizon.fiware_roles_workflow.get_role_element(step_slug, data_id);
    }*/

    var $permission_items = $("ul."+step_slug+"_permissions").children('li');
    $permission_items.each(function (idx, el) {
      if ($.inArray(($(el).data('permission-id')), permission_ids) !== -1) {
        $(el).addClass('active');
      } else {
        $(el).removeClass('active');
      }
    });
  },

  /*
   * Generates the HTML structure for a role's permissions that will be displayed
   * as a checkbox for each permission
   **/
  /*generate_permissions_element: function(step_slug, permission_ids) {
    var permissions = [],
      that = this,
      role_permissions = that.permissions[step_slug],
      p;

    for (p in role_permissions) {
      if (role_permissions.hasOwnProperty(p)){
        permissions.push({
          permission_id: p,
          permission_name: role_permissions[p],
        });
      }
    }

    var template = horizon.templates.compiled_templates["#fiware_roles_template"],
      params = {
        step_slug: step_slug,
        permissions: permissions,
      },
      role_el = $(template.render(params));
    this.update_role_permission_list(step_slug, permission_ids, role_el);
    return $(role_el);
  },*/

  /*
   * Generates the HTML structure for the role UI.
   **/
  /*generate_html: function(step_slug) {
    var data_id, data = horizon.fiware_roles_workflow.data[step_slug];
    for (data_id in data) {
      if(data.hasOwnProperty(data_id)){
        var display_name = data[data_id];
        var permission_ids = this.get_role_permissions(step_slug, data_id);
        if (permission_ids.length > 0) {
          $("." + step_slug + "_permissions").append(this.generate_permissions_element(step_slug, permission_ids));
        }
        else {
          $(".available_" + step_slug).append(this.generate_permissions_element(step_slug, permission_ids));
        }
      }
    }
    horizon.fiware_roles_workflow.detect_no_results(step_slug);
  },*/

  /*
   * Triggers on click of link to add/remove role association.
   **/
  /*update_role: function(step_slug) {
    $(".available_" + step_slug + ", ." + step_slug + "_roles").on('click', ".btn-group a[href='#add_remove']", function (evt) {
      evt.preventDefault();
      var available = $(".available_" + step_slug).has($(this)).length;
      var data_id = horizon.fiware_roles_workflow.get_field_id($(this).parent().siblings().attr('data-' + step_slug +  '-id'));
      var member_el = $(this).parent().parent();

      if (available) {
        var default_role = horizon.fiware_roles_workflow.default_permission_id[step_slug];
        //$(this).removeClass( "fa-plus" ).addClass( "fa-close" );
        $("." + step_slug + "_roles").append(member_el);
        horizon.fiware_roles_workflow.add_member_to_permission(step_slug, data_id, default_role);

        if (horizon.fiware_roles_workflow.has_permissions[step_slug]) {
          $(this).parent().siblings(".role_options").show();
          horizon.fiware_roles_workflow.update_role_permission_list(step_slug, data_id, [default_role], member_el);
        }
      }
      else {
        //$(this).removeClass( "fa-close" ).addClass( "fa-plus" );
        $(this).parent().siblings(".role_options").hide();
        $(".available_" + step_slug).append(member_el);
        horizon.fiware_roles_workflow.remove_role_from_permission(step_slug, data_id);
      }

      // update lists
      horizon.fiware_roles_workflow.list_filtering(step_slug);
      horizon.fiware_roles_workflow.detect_no_results(step_slug);

      // remove input filters
      $("input." + step_slug + "_filter").val("");
    });
  },*/

  /*
   * Detects whether each list has members and if it does not
   * displays a message to the user.
   **/
  /*detect_no_results: function (step_slug) {
    $('.' + step_slug +  '_filterable').each( function () {
      var css_class = $(this).find('ul').attr('class');
      // Example value: members step_slug_members
      // Pick the class name that contains the step_slug
      var filter = $.grep(css_class.split(' '), function(val){ return val.indexOf(step_slug) !== -1; })[0];

      if (!$('.' + filter).children('ul').length) {
        $('#no_' + filter).show();
        $("input[id='" + filter + "']").attr('disabled', 'disabled');
      }
      else {
        $('#no_' + filter).hide();
        $("input[id='" + filter + "']").removeAttr('disabled');
      }
    });
  },*/
  /*
   * Triggers on selecting a role to show its permissions
   **/
  show_role_permissions: function(step_slug) {
    $("input[type=radio]").on('change', function (evt) {
      if (!($(this).is(':checked'))) {
        return
      }
      // hide the message
      $("#" + step_slug + "_info_message").hide()
      // show permissions
      $("#" + step_slug + "_permissions").show()
      // mark active the ones owned
      var data_id = $(this).attr("data-" + step_slug + "-id");
      horizon.fiware_roles_workflow.update_role_permission_list(step_slug, data_id);
    });
  },
  /*
   * Triggers on selection of new permission for a role.
   **/
  select_role_permission: function(step_slug) {
    $("." + step_slug + "_permissions").on('click', 'li', function (evt) {
      evt.preventDefault();
      evt.stopPropagation();
      // get the newly selected permission and the role's name
      var new_permission_id = $(this).attr("data-permission-id");
      var id_str = $("#" + step_slug + "_roles").find('input[type=radio]:checked').attr("data-" + step_slug + "-id");
      var data_id = horizon.fiware_roles_workflow.get_field_id(id_str);
      // update permission lists
      if ($(this).hasClass('active')) {
        $(this).removeClass('active');
        horizon.fiware_roles_workflow.remove_role_from_permission(step_slug, data_id, new_permission_id);
      } else {
        $(this).addClass('active');
        horizon.fiware_roles_workflow.add_role_to_permission(step_slug, data_id, new_permission_id);
      }
      horizon.fiware_roles_workflow.update_role_permission_list(step_slug, data_id);
    });
  },
  /*
   * Inline edit for roles
   */
  inline_edit_role: {
    editing: false,
    init: function(step_slug) {
      var container = $("#" + step_slug + "_roles")
      // edit
      container.on('click', '.ajax-inline-edit', function (evt) {
        evt.preventDefault();
        console.log('edit')
        // first check if other element is on edit mode
        if (horizon.fiware_roles_workflow.inline_edit_role.editing){
          console.log('reset')
          // reset the edition of the other element
          var form_element = $(this).parent().siblings('.static_page');
          form_element.replaceWith(horizon.fiware_roles_workflow.inline_edit_role.cached_role);
        }
        horizon.fiware_roles_workflow.inline_edit_role.editing = true;
        //var data_id = $(this).siblings('input').attr("data-" + step_slug + "-id");
        //console.log('data_id:'+data_id)
        // TODO(garcianavalon) rename it, its a label...
        var role_div_element = $(this).parent();
        // save the element for later use
        horizon.fiware_roles_workflow.inline_edit_role.cached_role = role_div_element;
        // time to ajax for the form!
        var url = $(this).attr("href");
        horizon.fiware_roles_workflow.inline_edit_role.render_form(url, role_div_element)

      });
      // cancel
      container.on('click', '.inline-edit-cancel', function (evt) {
        console.log('cancel')
        evt.preventDefault();
        var form_element = $(this).parentsUntil(container, '.static_page');
        form_element.replaceWith(horizon.fiware_roles_workflow.inline_edit_role.cached_role);
        horizon.fiware_roles_workflow.inline_edit_role.editing = false;
      });
      // submit
      container.on('click', '.inline-edit-submit', function (evt) {
        evt.preventDefault();
        horizon.fiware_roles_workflow.inline_edit_role.submit_form(this, container);
      });
    },

    render_form: function(url, role_div_element) {
      horizon.ajax.queue({
        url: url,
        data: {},
        beforeSend: function () {
        },
        complete: function () {
        },
        error: function(jqXHR, status, errorThrown) {
          console.log('error')
          if (jqXHR.status === 401){
            var redir_url = jqXHR.getResponseHeader("X-Horizon-Location");
            if (redir_url){
              location.href = redir_url;
            } else {
              horizon.alert("error", gettext("Not authorized to do this operation."));
            }
          }
          else {
            if (!horizon.ajax.get_messages(jqXHR)) {
              // Generic error handler. Really generic.
              horizon.alert("error", gettext("An error occurred. Please try again later."));
            }
          }
        },
        success: function (data, textStatus, jqXHR) {
          console.log('success')
          //hide the role element, append the form in its place
          var form_element = $(data);
          $(role_div_element).replaceWith(form_element);
          form_element.focus();
          console.log('form rendered')
        }
      });
    },
    submit_form: function(el, container) {
      var form = $(el).parents('form').first();
      var form_element = $(el).parentsUntil(container, '.static_page');
      horizon.ajax.queue({
        type: 'POST',
        url: form.attr('action'),
        data: form.serialize(),
        beforeSend: function () {
        },
        complete: function () {
        },
        error: function(jqXHR, status, errorThrown) {
          console.log('error')
          if (jqXHR.status === 401){
            var redir_url = jqXHR.getResponseHeader("X-Horizon-Location");
            if (redir_url){
              location.href = redir_url;
            } else {
              horizon.alert("error", gettext("Not authorized to do this operation."));
            }
          }
          else {
            if (!horizon.ajax.get_messages(jqXHR)) {
              // Generic error handler. Really generic.
              horizon.alert("error", gettext("An error occurred. Please try again later."));
            }
          }
        },
        success: function (data, textStatus, jqXHR) {
          console.log('success')
          //hide the form, show the new element
          var role_element = horizon.fiware_roles_workflow.inline_edit_role.cached_role
          form_element.replaceWith(role_element);
          role_element.find('label').text(data);
          console.log('label:' +role_element.find('label').text())
          console.log('edited role!')
        }
      });
    },
  },
  /*
   * Triggers on the addition of a new member via the inline object creation field.
   **/
  /*
  add_new_member: function(step_slug) {
    $("select[id='id_new_" + step_slug + "']").on('change', function (evt) {
      // add the member to the visible list
      var display_name = $(this).find("option").text();
      var data_id = $(this).find("option").attr("value");
      var default_permission_id = horizon.fiware_roles_workflow.default_permission_id[step_slug];
      $("." + step_slug + "_roles").append(horizon.fiware_roles_workflow.generate_permissions_element(step_slug, display_name, data_id, [default_permission_id], "-"));

      // add the member to the hidden permission lists and the data list
      horizon.fiware_roles_workflow.data[step_slug][data_id] = display_name;
      $("select[multiple='multiple']").append("<option value='" + data_id + "'>" + horizon.fiware_roles_workflow.data[step_slug][data_id] + "</option>");
      horizon.fiware_roles_workflow.add_member_to_permission(step_slug, data_id, default_permission_id);

      // remove option from hidden select
      $(this).text("");

      // reset lists and input filters
      horizon.fiware_roles_workflow.list_filtering(step_slug);
      horizon.fiware_roles_workflow.detect_no_results(step_slug);
      $("input.filter").val("");

      // fix styling
      $("." +  step_slug + "_members .btn-group").removeClass('last_stripe');
      $("." +  step_slug + "_members .btn-group:last").addClass('last_stripe');
    });
  },*/


  /*
   * Calls set-up functions upon loading the workflow.
   **/
  workflow_init: function(modal, step_slug, step_id) {
      $(modal).find('form').each( function () {
      var $form = $(this);

      // Do nothing if this isn't a role modal
      /*if ($form.find('div.' + step_slug + '_role').length === 0) {
        return; // continue
      }*/

      // call the initialization functions
      horizon.fiware_roles_workflow.init_properties(step_slug);
      //horizon.fiware_roles_workflow.generate_html(step_slug);
      //horizon.fiware_roles_workflow.update_role(step_slug);
      horizon.fiware_roles_workflow.show_role_permissions(step_slug);
      horizon.fiware_roles_workflow.select_role_permission(step_slug);
      //horizon.fiware_roles_workflow.add_new_member(step_slug);
      horizon.fiware_roles_workflow.inline_edit_role.init(step_slug);

      // initially hide permissions list
      $form.find("#" +  step_slug + "_permissions").hide();

      // hide the dropdown for members too if we don't need to show it
      /*if (!horizon.fiware_roles_workflow.has_permissions[step_slug]) {
        $form.find("." + step_slug + "_members .role_options").hide();
      }*/

      // unfocus filter fields
      if (step_id.indexOf('update') === 0) {
        $form.find("#" + step_id + " input").blur();
      }

      // prevent filter inputs from submitting form on 'enter'
      // TODO(garcianavalon) check if we need this
      /*$form.find('.' + step_slug + '_role').keydown(function(event){
        if(event.keyCode === 13) {
          event.preventDefault();
          return false;
        }
      });*/

      // add filtering + styling to the inline obj creation btn
      //horizon.fiware_roles_workflow.add_new_member_styling(step_slug);
      //horizon.fiware_roles_workflow.list_filtering(step_slug);
      //horizon.fiware_roles_workflow.detect_no_results(step_slug);

      // fix initial striping of rows
      /*$form.find('.fake_' + step_slug + '_table').each( function () {
        var filter = "." + $(this).attr('id');
        $(filter + ' .btn-group:even').addClass('dark_stripe');
        $(filter + ' .btn-group:last').addClass('last_stripe');
      });*/
    });
  }
};
