describe("Messages (horizon.messages.js)", function () {
   var message;

   it("Basic Alert", function () {
      message = horizon.alert("success", "A message!");
      expect(message.hasClass("alert-success")).toBe(true);
      expect($('#main_content .messages .alert').length).toEqual(1);

      horizon.clearAllMessages();
      expect($('#main_content .messages .alert').length).toEqual(0);
   });

   it("Multiple Alerts", function () {
      message = horizon.alert("error", "An error!");
      expect(message.hasClass("alert-danger")).toBe(true);

      horizon.alert("success", "Another message");
      expect($('#main_content .messages .alert').length).toEqual(2);

      horizon.clearErrorMessages();
      expect($('#main_content .messages .alert-danger').length).toEqual(0);
      expect($('#main_content .messages .alert').length).toEqual(1);

      horizon.clearSuccessMessages();
      expect($('#main_content .messages .alert-success').length).toEqual(0);
      expect($('#main_content .messages .alert').length).toEqual(0);
   });

   it("Alert With HTML Tag", function () {
      var safe_string = "A safe message <a>here</a>!";
      message = horizon.alert("success", safe_string, "safe");
      expect(message.length).toEqual(1);
      expect(message.html().indexOf(safe_string)).not.toEqual(-1);
      expect($('#main_content .messages .alert').length).toEqual(1);
      horizon.clearAllMessages();
      expect($('#main_content .messages .alert').length).toEqual(0);
   });
});
