(function () {
  'use strict';

  describe('horizon.framework.util.workflow module', function () {
    it('should have been defined', function () {
      expect(angular.module('horizon.framework.util.workflow')).toBeDefined();
    });
  });

  describe('workflow factory', function () {
    var workflowService, spec;
    var decorators = [
      function (spec) {
        angular.forEach(spec.steps, function (step) {
          if (step.requireSomeServices) {
            step.checkReadiness = function () {};
          }
        });
      }
    ];

    beforeEach(module('horizon.framework'));

    beforeEach(inject(function ($injector) {
      workflowService = $injector.get('horizon.framework.util.workflow.service');
      spec = {
        steps: [
          { id: 'base_step_1', requireSomeServices: true },
          { id: 'base_step_2' },
          { id: 'base_step_3', requireSomeServices: true }
        ]
      };
    }));

    it('workflowService is defined', function () {
      expect(workflowService).toBeDefined();
    });

    it('workflowService is a function', function () {
      expect(angular.isFunction(workflowService)).toBe(true);
    });

    it('can be decorated', function () {
      workflowService(spec, decorators);
      var steps = spec.steps;

      expect(steps[0].checkReadiness).toBeDefined();
      expect(angular.isFunction(steps[0].checkReadiness)).toBe(true);

      expect(steps[1].checkReadiness).not.toBeDefined();

      expect(steps[2].checkReadiness).toBeDefined();
      expect(angular.isFunction(steps[2].checkReadiness)).toBe(true);
    });

    it('can be customized', function () {
      var workflow = workflowService(spec, decorators);
      expect(workflow.steps.length).toBe(3);
      expect(workflow.append).toBeDefined();
      expect(workflow.prepend).toBeDefined();
      expect(workflow.after).toBeDefined();
      expect(workflow.replace).toBeDefined();
      expect(workflow.remove).toBeDefined();
      expect(workflow.controllers).toBeDefined();
      expect(workflow.addController).toBeDefined();
      expect(workflow.initControllers).toBeDefined();
      expect(workflow.controllers.length).toBe(0);

      var last = { id: 'last' };
      workflow.append(last);
      expect(workflow.steps.length).toBe(4);
      expect(workflow.steps[3]).toBe(last);

      var first = { id: 'first' };
      workflow.prepend(first);
      expect(workflow.steps.length).toBe(5);
      expect(workflow.steps[0]).toBe(first);
      expect(workflow.steps[4]).toBe(last);

      var after = { id: 'after' };
      workflow.after('base_step_2', after);
      expect(workflow.steps.length).toBe(6);
      expect(workflow.steps[0]).toBe(first);
      expect(workflow.steps[3]).toBe(after);
      expect(workflow.steps[5]).toBe(last);

      var replace = { id: 'replace' };
      workflow.replace('base_step_1', replace);
      expect(workflow.steps.length).toBe(6);
      expect(workflow.steps[0]).toBe(first);
      expect(workflow.steps[1]).toBe(replace);
      expect(workflow.steps[3]).toBe(after);
      expect(workflow.steps[5]).toBe(last);

      workflow.remove('base_step_2');
      expect(workflow.steps.length).toBe(5);
      expect(workflow.steps[0]).toBe(first);
      expect(workflow.steps[1]).toBe(replace);
      expect(workflow.steps[2]).toBe(after);
      expect(workflow.steps[4]).toBe(last);

      workflow.addController('MyController');
      expect(workflow.controllers.length).toBe(1);
    });
  });
})();
