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
