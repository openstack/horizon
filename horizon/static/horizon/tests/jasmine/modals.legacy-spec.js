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
