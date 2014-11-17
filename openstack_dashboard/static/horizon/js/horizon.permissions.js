/* 
 * AJAX handling for permissions in my applications
 */

horizon.permissions = {
    _all_permissions : [],
    _role_permissions : [], //dictionary to store already loaded permissions for each role
    active_role : null
};

horizon.permissions.render_list = function () {
    //populate the table with all the permissions
    //checking the ones that are already assigned to the role
}

horizon.addInitFunction(function() {

 // AJAX loading of the role permissions
  $('input[type=radio][name=activeRole]').change( function (evt) {
    //get the active one
        //store it in active_role
    //check if the permissions lists is loaded
        //false->ajax load it
    //check if active role's permission list is already loaded
        //true-> render the list
    //false -> ajax request for the list of role-permission
    //then render the list
  });

  // AJAX give/remove permission to role using the checkbox
  $('.permission_check').change(function (evt) {
    //get the active permission
    //if selected
  });

  console.log('loaded permissions')
});

