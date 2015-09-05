describe("Client-Side Templating (horizon.templates.js)", function () {
  it("Compiled templates list should not be empty.", function () {
    var size = 0;
    angular.forEach(horizon.templates.compiled_templates, function () {
      size = size + 1;
    });
    expect(size).toBeGreaterThan(0);
  });
});
