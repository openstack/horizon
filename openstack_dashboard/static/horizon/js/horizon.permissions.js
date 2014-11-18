/* 
 * AJAX handling for permissions in myApplications
 */

horizon.permissions = {
    _all_permissions : null,
    _role_permissions : {}, //dictionary to store already loaded permissions for each role
    active_role : null
};

horizon.permissions.render_list = function () {
    //populate the table with all the permissions

    //checking the ones that are already assigned to the role
}

horizon.addInitFunction(function() {

  // AJAX loading of the role permissions
  $('input[type=radio][name=radio_roles]').change( function (evt) {
    //get the active one, store it in active_role
    var active_role = $('input[type=radio][name=radio_roles]:checked').val();
    horizon.permissions.active_role = active_role;
    console.log('active_role: '+ active_role);
    //check if the permissions lists is loaded
    if (horizon.permissions._all_permissions == null) {
        console.log('loading all permissions from server');
        //ajax
        console.log('loaded all permissions');
    }
    //check if active role's permission list is already loaded
    if (!(active_role in _role_permissions)){
        console.log('loading role '+ active_role +' permissions');
        //ajax request for the list of role-permission
        console.log('loaded role '+ active_role +' permissions');
    }
    //render the list
    console.log('rendering the role_permissions list');
    horizon.permissions.render_list();
    console.log('rendered!');
  });

  // AJAX give/remove permission to role using the checkbox
  $('.permission_check').change(function (evt) {
    //get the active permission
    //if selected
  });

  console.log('loaded permissions.js');
});

