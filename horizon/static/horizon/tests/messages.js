horizon.addInitFunction(function () {
    module("Messages (horizon.messages.js)");

    test("Basic Alert", function () {
        var message, message2;
        message = horizon.alert("success", "A message!");
        ok(message, "Create a success message.");
        ok(message.hasClass("alert-success"), 'Verify the message has the "alert-success" class.');
        equal($('#main_content .messages .alert').length, 1, "Verify our message was added to the DOM.");
        horizon.clearAllMessages();
        equal($('#main_content .messages .alert').length, 0, "Verify our message was removed.");
    });

    test("Multiple Alerts", function () {
        message = horizon.alert("error", "An error!");
        ok(message.hasClass("alert-error"), 'Verify the first message has the "alert-error" class.');

        message2 = horizon.alert("success", "Another message");
        equal($('#main_content .messages .alert').length, 2, "Verify two messages have been added to the DOM.");

        horizon.clearErrorMessages();
        equal($('#main_content .messages .alert-error').length, 0, "Verify our error message was removed.");
        equal($('#main_content .messages .alert').length, 1, "Verify one message remains.");
        horizon.clearSuccessMessages();
        equal($('#main_content .messages .alert-success').length, 0, "Verify our success message was removed.");
        equal($('#main_content .messages .alert').length, 0, "Verify no messages remain.");
    });
});
