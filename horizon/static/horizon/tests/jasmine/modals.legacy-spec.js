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

describe("Modals (horizon.modals.js)", function () {
  var modal, title, body, confirm;

  beforeEach(function () {
    title = "Test Title";
    body = "<p>Test Body</p>";
    confirm = "Test Confirm";
  });

  it("Modal Creation", function () {

    modal = horizon.modals.create(title, body, confirm);
    expect(modal.length).toEqual(1);

    modal = $("#modal_wrapper .modal");
    modal.modal();
    expect(modal.length).toEqual(1);
    expect(modal.hasClass("in")).toBe(true);
    expect(modal.find("h3").text()).toEqual(title);
    expect(modal.find(".modal-body").text().trim()).toEqual(body);
    expect(modal.find(".modal-footer .btn-primary").text()).toEqual(confirm);
    modal.find(".modal-footer .cancel").click();
    expect(modal.hasClass("in")).toBe(false);
  });
});
