/*
 *    (c) Copyright 2015 Hewlett-Packard Development Company, L.P.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

(function() {
  'use strict';

  angular
    .module('horizon.mock.openstack-service-api', [])
    .constant('initServices', initServices);

  function initServices($provide, apiService, toastService) {
    angular.extend(apiService, { get: angular.noop,
                   post: angular.noop,
                   put: angular.noop,
                   patch: angular.noop,
                   delete: angular.noop });
    angular.extend(toastService, { add: angular.noop });
    $provide.value('horizon.framework.util.http.service', apiService);
    $provide.value('horizon.framework.widgets.toast.service', toastService);

    return testCall;
  }

  /*
   This function tests the 'typical' way that apiService calls are made.
   Look at this typical approach:

   this.getVolumes = function(params) {
     var config = (params) ? {'params': params} : {};
     return apiService.get('/api/cinder/volumes/', config)
                      .error(function () {
                        toastService.add('error', gettext('Unable to retrieve the volumes.'));
                      });
    }

    In this case there is an apiService call that is made with one or two
    arguments, and on error a function is called that invokes the
    toastService's add method.

    The function below takes in the set of variables, both input and output,
    that are required to test the above code.  It spies on the apiService
    method that is called, and also spies on its returned simulated promise
    'error' method.

    Having established those spies, the code then inspects the parameters
    passed to the apiService, as well as the results of those methods.
    Then the code invokes of function passed to the error handler, and
    ensures that the toastService is called with the appropriate parameters.
  */
  function testCall(apiService, service, toastService, config) {
    // 'promise' simulates a promise, including a self-referential success
    // handler.
    var promise = {error: angular.noop, success: function() {
      return this;
    }};
    spyOn(apiService, config.method).and.returnValue(promise);
    spyOn(promise, 'error');
    service[config.func].apply(null, config.testInput);

    // Checks to ensure we call the api service with the appropriate
    // parameters.
    if (angular.isDefined(config.call_args)) {
      expect(apiService[config.method].calls.mostRecent().args).toEqual(config.call_args);
    } else if (angular.isDefined(config.data)) {
      expect(apiService[config.method]).toHaveBeenCalledWith(config.path, config.data);
    } else {
      expect(apiService[config.method]).toHaveBeenCalledWith(config.path);
    }

    // The following retrieves the first argument of the first call to the
    // error spy.  This exposes the inner function that, when invoked,
    // allows us to inspect the error call and the message given.
    var innerFunc = promise.error.calls.argsFor(0)[0];
    expect(innerFunc).toBeDefined();
    spyOn(toastService, 'add');
    innerFunc();
    expect(toastService.add).toHaveBeenCalledWith(config.messageType || 'error', config.error);
  }

})();
