/* Namespace for core functionality related to Role-Permission Workflow Step.
 * Based on the membership step. 
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
    //horizon.fiware_roles_workflow.has_permissions[step_slug] = $("." + step_slug + "_membership").data('show-roles') !== "False";
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
    var members_list = [];
    var permission_name, permission_id, selected_members;
    angular.forEach(this.get_permission_element(step_slug, ''), function(value, key) {
      permission_id = horizon.fiware_roles_workflow.get_field_id($(value).attr('id'));
      permission_name = $('label[for="id_' + step_slug + '_permission_' + permission_id + '"]').text();

      // get the array of members who are selected in this list
      selected_members = $(value).find("option:selected");
      // extract the member names and add them to the dictionary of lists
      members_list = [];
      if (selected_members) {
        angular.forEach(selected_members, function(member) {
          members_list.push(member.value);
        });
      }
      horizon.fiware_roles_workflow.current_relations[step_slug][permission_id] = members_list;
    });
  },

  /*
   * Returns the ids of permissions the data is member of.
   **/
  get_member_permissions: function(step_slug, data_id) {
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
   * Helper function for remove_member_from_permission.
   **/
  remove_member: function(step_slug, data_id, permission_id, permission_list) {
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
  remove_member_from_permission: function(step_slug, data_id, permission_id) {
    var permission, membership = horizon.fiware_roles_workflow.current_relations[step_slug];
    if (permission_id) {
      horizon.fiware_roles_workflow.remove_member(
        step_slug, data_id, permission_id, membership[permission_id]
      );
    }
    else {
      // search for membership in permission lists
      for (permission in membership) {
        if (membership.hasOwnProperty(permission)) {
          horizon.fiware_roles_workflow.remove_member(
            step_slug, data_id, permission,  membership[permission]
          );
        }
      }
    }
  },

  /*
   * Adds a member to a given permission list.
   **/
  add_member_to_permission: function(step_slug, data_id, permission_id) {
    var permission_list = horizon.fiware_roles_workflow.current_relations[step_slug][permission_id];
    permission_list.push(data_id);
    horizon.fiware_roles_workflow.update_permission_lists(step_slug, permission_id, permission_list);
  },

  /*update_role_permission_list: function(step_slug, permission_ids, member_el) {
    if (typeof(permission_ids) === 'undefined') {
      permission_ids = horizon.fiware_roles_workflow.get_member_permissions(step_slug, data_id);
    }
    if (typeof(member_el) === 'undefined') {
      member_el = horizon.fiware_roles_workflow.get_member_element(step_slug, data_id);
    }

    var $dropdown = member_el.find("li.member").siblings('.dropdown');
    var $permission_items = $dropdown.children('.role_dropdown').children('li');

    $permission_items.each(function (idx, el) {
      if ($.inArray(($(el).data('role-id')), permission_ids) !== -1) {
        $(el).addClass('selected');
      } else {
        $(el).removeClass('selected');
      }
    });

    // set the selection back to default role
    var $permissions_display = $dropdown.children('.dropdown-toggle').children('.roles_display');
    /*var roles_to_display = [];
    for (var i = 0; i < permission_ids.length; i++) {
      if (i === 2) {
        roles_to_display.push('...');
        break;
      }
      roles_to_display.push(horizon.fiware_roles_workflow.permissions[step_slug][permission_ids[i]]);
    }
    text = roles_to_display.join(', ');
    if (text.length === 0) {
      text = gettext('No permissions');
    }
    text = permission_ids.length > 0 ? permission_ids.length + " permissions" : "No permissions";
    $permissions_display.text(text);
  },*/

  /*
   * Generates the HTML structure for a role's permissions that will be displayed
   * as a checkbox for each permission
   **/
  generate_permissions_element: function(step_slug, permission_ids) {
    var permissions = [],
      that = this,
      membership_permissions = that.permissions[step_slug],
      p;

    for (p in membership_permissions) {
      if (membership_permissions.hasOwnProperty(p)){
        permissions.push({
          permission_id: p,
          permission_name: membership_permissions[p],
          status: 'active',
        });
      }
    }

    var template = horizon.templates.compiled_templates["#fiware_roles_template"],
      params = {
        step_slug: step_slug,
        permissions: permissions,
      },
      member_el = $(template.render(params));
    //this.update_role_permission_list(step_slug, permission_ids, member_el);
    return $(member_el);
  },

  /*
   * Generates the HTML structure for the membership UI.
   **/
  /*generate_html: function(step_slug) {
    var data_id, data = horizon.fiware_roles_workflow.data[step_slug];
    for (data_id in data) {
      if(data.hasOwnProperty(data_id)){
        var display_name = data[data_id];
        var permission_ids = this.get_member_permissions(step_slug, data_id);
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
   * Triggers on click of link to add/remove membership association.
   **/
  /*update_membership: function(step_slug) {
    $(".available_" + step_slug + ", ." + step_slug + "_members").on('click', ".btn-group a[href='#add_remove']", function (evt) {
      evt.preventDefault();
      var available = $(".available_" + step_slug).has($(this)).length;
      var data_id = horizon.fiware_roles_workflow.get_field_id($(this).parent().siblings().attr('data-' + step_slug +  '-id'));
      var member_el = $(this).parent().parent();

      if (available) {
        var default_role = horizon.fiware_roles_workflow.default_permission_id[step_slug];
        //$(this).removeClass( "fa-plus" ).addClass( "fa-close" );
        $("." + step_slug + "_members").append(member_el);
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
        horizon.fiware_roles_workflow.remove_member_from_permission(step_slug, data_id);
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
  show_active_role_permissions: function(step_slug) {
    $("input[type=radio]").on('change', function (evt) {
      if (!($(this).is(':checked'))) {
        return
      }
      evt.preventDefault();
      var data_id;
      var active_role_id = $(this).parent().parent().attr("data-" + step_slug + "-id");
      var data = horizon.fiware_roles_workflow.data[step_slug];
      for (data_id in data) {
        if (data.hasOwnProperty(data_id) && active_role_id == data_id) {
          var permission_ids = horizon.fiware_roles_workflow.get_member_permissions(step_slug, data_id);
          var permissions_container = $("." + step_slug + "_permissions")
          permissions_container.html(horizon.fiware_roles_workflow.generate_permissions_element(step_slug, permission_ids));
        }
      }
    });
  },
  /*
   * Triggers on selection of new permission for a member.
   **/
  select_member_permission: function(step_slug) {
    $(".available_" + step_slug + ", ." + step_slug + "_members").on('click', '.role_dropdown li', function (evt) {
      evt.preventDefault();
      evt.stopPropagation();

      // get the newly selected permission and the member's name
      var new_permission_id = $(this).attr("data-permission-id");
      var id_str = $(this).parent().parent().siblings(".member").attr("data-" + step_slug + "-id");
      var data_id = horizon.fiware_roles_workflow.get_field_id(id_str);
      // update permission lists
      if ($(this).hasClass('selected')) {
        $(this).removeClass('selected');
        horizon.fiware_roles_workflow.remove_member_from_permission(step_slug, data_id, new_permission_id);
      } else {
        $(this).addClass('selected');
        horizon.fiware_roles_workflow.add_member_to_permission(step_slug, data_id, new_permission_id);
      }
      //horizon.fiware_roles_workflow.update_role_permission_list(step_slug, data_id);
    });
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
      $("." + step_slug + "_members").append(horizon.fiware_roles_workflow.generate_permissions_element(step_slug, display_name, data_id, [default_permission_id], "-"));

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
   * Style the inline object creation button, hide the associated field.
   **/
  /*add_new_member_styling: function(step_slug) {
    var add_member_el = $("label[for='id_new_" + step_slug + "']").parent();
    $(add_member_el).find("select").hide();
    $("#add_" + step_slug).append($(add_member_el));
    $(add_member_el).addClass("add_" + step_slug);
    $(add_member_el).find("label, .input").addClass("add_" + step_slug + "_btn");
  },*/

  /*
   * Fixes the striping of the fake table upon modification of the lists.
   **/
  /*fix_stripes: function(step_slug) {
    $('.fake_' + step_slug + '_table').each( function () {
      var filter = "." + $(this).attr('id');
      var visible = " .btn-group:visible";
      var even = " .btn-group:visible:even";
      var last = " .btn-group:visible:last";

      // fix striping of rows
      $(filter + visible).removeClass('dark_stripe');
      $(filter + visible).addClass('light_stripe');
      $(filter + even).removeClass('light_stripe');
      $(filter + even).addClass('dark_stripe');

      // fix bottom border of new last element
      $(filter + visible).removeClass('last_stripe');
      $(filter + last).addClass('last_stripe');
    });
  },*/

  /*
   * Sets up filtering for each list of data.
   **/
  /*list_filtering: function (step_slug) {
    // remove previous lists' quicksearch events
    $('input.' + step_slug + '_filter').unbind();

    // set up quicksearch to filter on input
    $('.' + step_slug + '_filterable').each(function () {
      var css_class = $(this).children().children('ul').attr('class');
      // Example value: members step_slug_members
      // Pick the class name that contains the step_slug
      var filter = $.grep(css_class.split(' '), function(val){ return val.indexOf(step_slug) !== -1; })[0];

      var input = $("input[id='" + filter +"']");
      input.quicksearch('ul.' + filter + ' ul li span.display_name', {
        'delay': 200,
        'loader': 'span.loading',
        'show': function () {
          $(this).parent().parent().show();
          if (filter === "available_" + step_slug) {
            $(this).parent('.dropdown-toggle').hide();
          }
        },
        'hide': function () {
          $(this).parent().parent().hide();
        },
        'noResults': 'ul#no_' + filter,
        'onAfter': function () {
          horizon.fiware_roles_workflow.fix_stripes(step_slug);
        },
        'prepareQuery': function (val) {
          return new RegExp(val, "i");
        },
        'testQuery': function (query, txt, span) {
          if ($(input).attr('id') === filter) {
            $(input).prev().removeAttr('disabled');
            return query.test($(span).text());
          } else {
            return true;
          }
        }
      });
    });
  },*/

  /*
   * Calls set-up functions upon loading the workflow.
   **/
  workflow_init: function(modal, step_slug, step_id) {
      $(modal).find('form').each( function () {
      var $form = $(this);

      // Do nothing if this isn't a membership modal
      /*if ($form.find('div.' + step_slug + '_membership').length === 0) {
        return; // continue
      }*/

      // call the initialization functions
      horizon.fiware_roles_workflow.init_properties(step_slug);
      //horizon.fiware_roles_workflow.generate_html(step_slug);
      //horizon.fiware_roles_workflow.update_membership(step_slug);
      horizon.fiware_roles_workflow.show_active_role_permissions(step_slug);
      horizon.fiware_roles_workflow.select_member_permission(step_slug);
      //horizon.fiware_roles_workflow.add_new_member(step_slug);


      // initially hide role dropdowns for available member list
      // TODO(garcianavalon) hide the permission checkboxes list instead
      $form.find(".available_" +  step_slug + " .role_options").hide();

      // hide the dropdown for members too if we don't need to show it
      /*if (!horizon.fiware_roles_workflow.has_permissions[step_slug]) {
        $form.find("." + step_slug + "_members .role_options").hide();
      }*/

      // unfocus filter fields
      if (step_id.indexOf('update') === 0) {
        $form.find("#" + step_id + " input").blur();
      }

      // prevent filter inputs from submitting form on 'enter'
      // TODO(garcianavalon) check if we need this, (don't forget there is 
      // no _membership in template anymore)
      $form.find('.' + step_slug + '_membership').keydown(function(event){
        if(event.keyCode === 13) {
          event.preventDefault();
          return false;
        }
      });

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
