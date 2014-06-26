/*
    @author  :  Maninder Rajpal 
*/

$(document).ready(function() {
    
    registrationForm = function() {
        $("#jcRegistrationFrm").validate({
            rules: {
                first_name: {
                    required: true,
                    minlength: 1
                },
                // last_name: {
                //     required: true,
                //     minlength: 1
                // },
                email: {
                    required: true,
                    email: true,
                },
                // confirm_email: {
                //     required: true,
                //     equalTo: "#id_email"
                // },
                password: {
                    required: true,
                    minlength: 6
                },
                // confirm_password: {
                //     required: true,
                //     minlength: 6,
                //     equalTo: "#id_password"
                // },
                // company: {
                //     required: true
                // },
                // address: {
                //     required: true
                // },
                // country: {
                //     required: true
                // },
                // state: {
                //     required: true
                // },
                // city: {
                //     required: true
                // },
                // pincode: {
                //     required: true,
                //     digits: true
                // },
                // country_code: {
                //     required: true
                // },
                phone: {
                    required: true,
                    digits: true,
                    minlength: 10
                },
                // termscond: {
                //     required: true
                // }               
            },
            messages: {
                first_name: {
                    //required: "Please enter First Name",
                    minlength: "Your First Name must consist of at least 1 characters"
                },
                // last_name: {
                //     minlength: "Your Last Name must consist of at least 1 characters"
                // },
                password: {
                    minlength: "Your password must be at least 6 characters long"
                },
                phone: {
                    minlength: "Please enter a valid phone number: (e.g. 9999999999)"
                }
            }
        });
    };

});




$(document).ready(function(event) {
	$("#menu").menu();
	registrationForm();

    $(document).on('change', '#id_country', function() {
        $.ajax({
             type: 'GET',
             url: '/regions/' + $(this).val() + '/',
             data: {},
             success: function(data, textStatus, request) {
                        var state = $('#id_state');
                        state.html(data);
                        state.trigger("change");
                     },
             error: function(request, textStatus, error) {
                //todo
             }
        });//ajax
    });

    $(document).on('change', '#id_state', function() {
        $.ajax({
             type: 'GET',
             url: '/cities/' + $(this).val() + '/',
             data: {},
             success: function(data, textStatus, request) {
                        var state = $('#id_city');
                        state.html(data);
                     },
             error: function(request, textStatus, error) {
                //todo
             }
        });//ajax
    });
});

