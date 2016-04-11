/*
 *    (c) Copyright 2015 Hewlett Packard Enterprise Development Company LP
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

  angular.module('horizon.framework.conf')

  .factory('horizon.framework.conf.resource-type-registry.service', registryService);

  registryService.$inject = [
    'horizon.framework.util.extensible.service'
  ];

  /*
   * @ngdoc service
   * @name horizon.framework.conf.resource-type-registry.service
   * @description
   * This service provides a registry which allows for registration of
   * configurations for resource types.  The purpose of these registrations
   * is to make it easy for modules to register a variety of common features
   * that are used both in display and behavior related to resource types.
   * Ideally the primary members of a resource type are decided on by
   * the community; however it is possible using a configuration to add
   * all kinds of members to the resource type.
   * Common elements in resource type configurations include things like
   * batch and item actions, which are associated with the resource type
   * via a key.  The key follows the format: OS::Glance::Image.
   * The functions that are exposed both assist with registration and also
   * provide utilities relevant for their consumption.
   * This service uses the extensibility service to decorate the individual
   * containers for the actions, so they may be best manipulated via its
   * decorated methods.
   * The concept for use is to register actions with the resource types at
   * the Angular module level, using the .run() function.  This allows
   * actions to be configured by any module.
   * Actions should not perform complex actions in their construction, for
   * example API calls, because as injectables their constructor is run
   * during injection, meaning API calls would be executed as the module
   * is initialized.  This would mean those calls would be executed on any
   * Angular context initialization, such as going to the login page.  Actions
   * should instead place such code in their initScope() functions.
   */
  function registryService(extensibleService) {

    function ResourceType() {
      // 'properties' contains information about properties associated with
      // this resource type.  The expectation is that the key is the 'code'
      // name of the property and the value conforms to the standard
      // described in the setProperty() function below.
      var properties = {};
      this.setProperty = setProperty;
      this.getName = getName;
      this.label = label;
      this.format = format;

      // itemActions is a list of actions that can be executed upon a single
      // item.  The list is made extensible so it can be added to independently.
      this.itemActions = [];
      extensibleService(this.itemActions, this.itemActions);

      // batchActions is a list of actions that can be executed upon multiple
      // items.  The list is made extensible so it can be added to independently.
      this.batchActions = [];
      extensibleService(this.batchActions, this.batchActions);

      /**
       * @ngdoc function
       * @name setProperty
       * @description
       * Adds a property to the resource type object.  Replaces any existing
       * definition.  These calls can be chained to other ResourceType
       * functions.  Specific information about the logic and evaluation of
       * the property attributes is more fully described in the
       * format() function.
       * @example
       ```
       resourceType.setProperty("kernel_id", {
         label: gettext("Kernel ID")  // just provides the label.
                                      // values will be shown directly
       })
         .setproperty("disk_size", {
           label: gettext("disk size"),
           value_function: function(size) {      // uses function to
             return interpolate("%s GiB", size); // display values.
           }
         })
         .setproperty("disk_size", {
           label: gettext("disk size"),
           value_function: [
             function(size) {                      // uses multiple
               return input.replace(/-/, ' ');     // functions in sequence
             },                                    // to display values.
             function(input) {
               return input.toUpperCase();
             }
           ]
         })
         .setProperty("status", {
           label: gettext("Status"),
           value_mapping: {                  // uses mapping to
             ready: gettext("Ready"),        // look up values
             waiting: gettext("Waiting")
           },
           default_value: gettext("Unknown") // uses default if no match
         })
         .setProperty("state", {
           label: gettext("State"),
           value_mapping: {                  // uses mapping to
             initial: gettext("Initial"),    // look up values
             running: gettext("Running")
           },
           default_function: function(input) { // uses function if no match
             return input.toUpperCase();
           }
         })
          )
       ```
       */
      function setProperty(name, prop) {
        properties[name] = prop;
        return this;
      }

      /**
       * @ngdoc function
       * @name getName
       * @description
       * Given a count, returns the appropriate name (e.g. singular or plural)
       * @example
       ```
       var resourceType = getResourceType('thing', {
         names: [gettext('Thing'), gettext('Things')]
       });

       var singleName = resourceType.getName(1); // returns singular
       ```
       */
      function getName(count) {
        if (this.names) {
          return ngettext.apply(null, this.names.concat([count]));
        }
      }

      /**
       * @ngdoc function
       * @name label
       * @description
       * Returns a human-appropriate label for the given name.
       * @example
       ```
       var name = resourceType.propLabel('disk_format'); // Yields 'Disk Format'
       ```
       */
      function label(name) {
        var prop = properties[name];
        if (angular.isDefined(prop) && angular.isDefined(prop.label)) {
          return prop.label;
        }
        return name;
      }

      /**
       * @ngdoc function
       * @name format
       * @description
       * Returns a well-formatted value given a property name and an
       * associated value.
       * The formatting is determined by evaluating various options on the
       * property.
       *
       * 'value_function' provides a single or a list of functions that will
       * evaluate the source value as input and return output; or in the case
       * of multiple functions, will chain the output of one to the input of
       * the next.
       *
       * 'value_mapping' provides a hash where, if a matching key is found,
       * the value is returned.  If no matching key is found, then if
       * 'value_mapping_default_function' is present, the value is passed
       * to the function and the result is returned.  Finally, if there was
       * no matching key and no default function, 'value_mapping_default_value'
       * provides a string to be returned.
       *
       * If these options are not present, the original value is returned.
       * value.
       * @example
       ```
       var value = resourceType.format('disk_size', 12); // Yields '12 GiB'
       ```
       */
      function format(name, value) {
        var prop = properties[name];
        if (angular.isUndefined(prop)) {
          // no property definition; return the original value.
          return value;
        } else if (prop.value_function) {
          if (angular.isArray(prop.value_function)) {
            return prop.value_function.reduce(function execEach(prev, func) {
              return func(prev);
            }, value);
          } else {
            return prop.value_function(value);
          }
        } else if (prop.value_mapping) {
          if (angular.isDefined(prop.value_mapping[value])) {
            return prop.value_mapping[value];
          } else if (angular.isDefined(prop.value_mapping_default_function)) {
            return prop.value_mapping_default_function(value);
          } else if (angular.isDefined(prop.value_mapping_default_value)) {
            return prop.value_mapping_default_value;
          }
        }
        // defaults to simply returning the original value.
        return value;
      }
    }

    var resourceTypes = {};
    var registry = {
      getResourceType: getResourceType,
      initActions: initActions
    };

    /*
     * @ngdoc function
     * @name getResourceType
     * @description
     * Retrieves all information about a resource type.  If the resource
     * type doesn't exist in the registry, this creates a new entry.
     * If a configuration is supplied, the resource type is extended to
     * use the configuration's properties.
     */
    function getResourceType(type, config) {
      if (!resourceTypes.hasOwnProperty(type)) {
        resourceTypes[type] = new ResourceType();
      }
      if (angular.isDefined(config)) {
        angular.extend(resourceTypes[type], config);
      }
      return resourceTypes[type];
    }

    /*
     * @ngdoc function
     * @name initActions
     * @description
     * Performs initialization (namely, scope-setting) of all actions
     * for the given type.  This requires the proper scope be passed.
     * If an action does not have an initScope() function, it is ignored.
     */
    function initActions(type, scope) {
      angular.forEach(resourceTypes[type].itemActions, setActionScope);
      angular.forEach(resourceTypes[type].batchActions, setActionScope);

      function setActionScope(action) {
        if (action.service.initScope) {
          action.service.initScope(scope.$new());
        }
      }
    }

    return registry;
  }

})();
