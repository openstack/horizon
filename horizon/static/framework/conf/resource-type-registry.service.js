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
    'horizon.framework.util.extensible.service',
    '$log'
  ];

  /*
   * @ngdoc service
   * @name horizon.framework.conf.resource-type-registry.service
   * @description
   *
   * The type registry collects up implementation details for client-side user
   * interface, for example, the angular panels in Horizon. It provides a single
   * location for common features that are used in display and behavior related
   * to that resource type. These are tied to types using the HEAT type names,
   * for example, 'OS::Glance::Image', so types encapsulate a single object
   * retrieved from a service API. Other types might include Nova servers or
   * Swift objects. The HEAT type names are listed:
   *
   *   https://docs.openstack.org/heat/latest/template_guide/openstack.html
   *
   * Each resource type is a singleton; to create or retrieve the type use:
   *
   *   var resourceType = registryService.getResourceType('OS::Glance::Image');
   *
   * Types may have a number of aspects associated with them:
   *
   * - a simplified name for the type.
   * - a mechanism for retrieving objects of the type by id and listing objects
   * - actions that may be performed on individual objects, multiple (batch)
   *   objects, and globally (independent of any existing objects; e.g. Create
   *   Image)
   * - details view(s) for individual objects (multiple views will be in tabs)
   * - information about properties, including:
   *   - labels used in places like table headers or forms
   *   - formatting mechanisms for property values
   *
   * Types should be defined at the Angular module level, using the .run() function.
   * This allows actions to be configured (and extended) by any module.
   */
  function registryService(extensibleService, $log) {

    function ResourceType(typeCode) {
      /*
       * @ngdoc method
       * @name ResourceType
       * @description
       *
       * A singleton instance of ResourceType is returned by the
       * registryService.getResourceType(typeCode) call.
       *
       * These array properties which use Horizon's extensibility service:
       *
       * itemActions -- allowed "row" type actions for an <actions> directive.
       *
       * batchActions -- allowed "batch" type actions for an <actions> directive.
       *
       * globalActions -- actions that don't require an item argument. These could
       *   be used in an <actions> directive using the "batch" type, even though
       *   no items will be passed to them.
       *
       * detailsViews -- views for a <hz-details> directive.
       *
       * tableColumns -- columns for a <hz-dynamic-table> directive. Note that
       *   getTableColumns() is provided as a convenience for listing those columns
       *   with the title property automatically filled in.
       *
       * filterFacets - filter facets registered here may be used in a <magic-search>
       *   bar.
       */
      var self = this;    // disambiguate uses of "this" later in this code

      // these are kept private so that multiple registrations of a ResourceType
      // won't clobber each other
      var names = [];
      var properties = {};

      self.type = typeCode;
      self.initActions = initActions;
      self.setProperty = setProperty;
      self.setProperties = setProperties;
      self.getProperties = getProperties;
      self.getName = getName;
      self.setNames = setNames;
      self.label = label;
      self.load = defaultLoadFunction;
      self.setLoadFunction = setLoadFunction;
      self.isLoadFunctionSet = isLoadFunctionSet;
      self.list = defaultListFunction;
      self.setListFunction = setListFunction;
      self.isListFunctionSet = isListFunctionSet;
      self.itemInTransitionFunction = defaultItemInTransitionFunction;
      self.setItemInTransitionFunction = setItemInTransitionFunction;
      self.itemName = itemName;
      self.setItemNameFunction = setItemNameFunction;
      self.setPathParser = setPathParser;
      self.parsePath = parsePath;
      self.setPathGenerator = setPathGenerator;
      self.path = path;
      self.needsFilterFirstFunction = defaultNeedsFilterFirstFunction;
      self.setNeedsFilterFirstFunction = setNeedsFilterFirstFunction;

      self.itemActions = [];
      extensibleService(self.itemActions, self.itemActions);
      self.batchActions = [];
      extensibleService(self.batchActions, self.batchActions);
      self.globalActions = [];
      extensibleService(self.globalActions, self.globalActions);
      self.detailsViews = [];
      extensibleService(self.detailsViews, self.detailsViews);
      self.tableColumns = [];
      extensibleService(self.tableColumns, self.tableColumns);
      self.getTableColumns = getTableColumns;
      self.filterFacets = [];
      extensibleService(self.filterFacets, self.filterFacets);

      self.summaryTemplateUrl = false;
      self.setSummaryTemplateUrl = setSummaryTemplateUrl;

      self.defaultIndexUrl = false;
      self.setDefaultIndexUrl = setDefaultIndexUrl;
      self.getDefaultIndexUrl = getDefaultIndexUrl;

      // Function declarations

      /*
       * @ngdoc function
       * @name initActions
       * @description
       * Performs initialization of all actions for the given type.
       *
       * If an action does not have an initAction() function, it is ignored.
       */
      function initActions() {
        angular.forEach(self.itemActions, setActionScope);
        angular.forEach(self.batchActions, setActionScope);
        angular.forEach(self.globalActions, setActionScope);

        function setActionScope(action) {
          if (action.service.initAction) {
            action.service.initAction();
          }
        }
      }

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
       .setProperty("disk_size", {
         label: gettext("disk size")
       })
       .setProperty("disk_size", {
         label: gettext("disk size")
       })
       .setProperty("status", {
         label: gettext("Status")
       })
       .setProperty("state", {
         label: gettext("State")
       });
       ```
       */
      function setProperty(name, prop) {
        properties[name] = prop;
        return self;
      }

      /**
       * @ngdoc function
       * @name setProperties
       * @description
       * Syntactic sugar for setProperty.
       * Allows an object of properties where the key is the id and the value
       * can either be a string or an object. If the value is a string, we assume
       * that it is the label. If the value is an object, we use the object as
       * the property for that key.
       * @example
       ```
       var properties = {
         id: gettext('ID'),
         enabled: { label: gettext('Enabled') }
       };
       resourceType.setproperties(properties);
       */
      function setProperties(properties) {
        angular.forEach(properties, function(value, key) {
          var prop = angular.isString(value) ? { label: value } : value;
          setProperty(key, prop);
        });
        return this;
      }

      /**
       * Return a copy of any properties that have been registered.
       * @returns {*}
       */
      function getProperties() {
        return angular.copy(properties);
      }

      /**
       * @ngdoc function
       * @name setListFunction
       * @description
       * Sets the list() function that returns a promise, that resolves with a list
       * of all the items of a given type.
       *
       * The function will be called with an object with key:value string
       * pairs to use when limiting the list of items. This could be the result
       * of a magic search filter.
       *
       * @example
       ```
       resourceType.setListFunction(func);

       function func(params) {
         return someApi.getItems(params);
       }

       var listPromise = resourceType.list({name: 'bob', active: 'yes'});
       ```
       */
      function setListFunction(func) {
        self.list = func;
        return self;
      }

      /**
       * True if a list function for this resource has been registered.
       * @returns {boolean}
       */
      function isListFunctionSet() {
        return self.list !== defaultListFunction;
      }

      /**
       * @ngdoc function
       * @name list
       * @description
       * List all the items of this type. The implementation for this
       * function *must* be supplied with setListFunction()
       *
       * @example
       ```
       var listPromise = resourceType.list();
       ```
       */
      function defaultListFunction() {
        $log.error('No list function defined for', typeCode);
        return Promise.reject({data: {items: []}});
      }

      /**
       * @ngdoc function
       * @name defaultItemInTransitionFunction
       * @description
       * A default implementation for the "itemInTransitionFunction function-pointer" which
       * returns false every time.
       * @returns {boolean}
       */
      function defaultItemInTransitionFunction() {
        return false;
      }

      /**
       * Set a function that detects if an instance of this resource type is in a
       * "transition" state, such as an image with a "queued" status, or an instance
       * with an "in-progress" status. For example, this might be used to highlight
       * a particular item in a list, or to set a progress indicator when viewing that
       * items details.
       *
       * By default, a call to itemInTransitionFunction(item) will return false unless this
       * function is registered for the resource type;
       *
       * @ngdoc function
       * @param func - The callback-function to be used for determining if this
       * resource is in a transitional state.  This callback-function will be passed
       * an object that is an instance of this resource (e.g. an image) and should
       * return a boolean.  "true" indicates the item is in a "transition" state.
       * @returns {ResourceType} - returning self to facilitate call-chaining.
       */
      function setItemInTransitionFunction(func) {
        self.itemInTransitionFunction = func;
        return self;
      }

      /**
       * @ngdoc function
       * @name getTableColumns
       * @description
       * Provides the table columns for this type and generates a 'title'
       * if not already present, using the label provided for
       * the ResourceType's property in the column. The output of this
       * function supplied to hz-dynamic-table as config.columns
       * @example
       ```
       resourceType.setProperty('owner', {
        label: gettext('Owner')
       });
       resourceType.tableColumns.append({'id': 'owner'});  // no 'title'

       var columns = resourceType.getTableColumns();
       // columns[0] will contain {'id': 'owner', 'title': 'Owner'}
       ```
       */
      function getTableColumns() {
        return self.tableColumns.map(mapTableInfo);

        function mapTableInfo(x) {
          var tableInfo = x;
          tableInfo.title = x.title || label(x.id);
          // use 'values' or 'filters' from property definition if available.
          if (properties[x.id] && properties[x.id].values) {
            tableInfo.values = properties[x.id].values;
          }
          if (properties[x.id] && properties[x.id].filters) {
            tableInfo.filters = properties[x.id].filters;
          }
          return tableInfo;
        }
      }

      /**
       * @ngdoc function
       * @name setPathParser
       * @description
       * Sets the parsePath function that is used to parse paths.
       *
       * Given a subpath (a part of a URL), the parser should produce
       * an object that describes an item enough to load it using
       * load() - typically this will be an id string, but load()
       * may require a more complex object.
       * @example
       ```
       resourceType.setPathParser(func);

       function func(path) {
         return path.replace('-', '');
       }

       var descriptor = resourceType.parsePath(path);
       var item = resourceType.load(descriptor);
       ```
       */
      function setPathParser(func) {
        self.parsePath = func;
        return self;
      }

      /**
       * @ngdoc function
       * @name parsePath
       * @description
       * The default implementation of parsePath just returns the
       * subpath, assuming that it is an id.
       *
       * Path generation and parsing is used to enable identification and retrieval
       * of resource items from URL fragments (subpaths). The path will commonly be
       * used as part of a details route, and in most cases will consist of just
       * the item's id. For example an item with identifier of 'abc-defg' would
       * yield a subpath 'abc-defg' which could be used in a details route,
       * such as: '/details/OS::Glance::Image/abc-defg'. See parsePath() and path()
       * for more information.
       *
       * Replace the default implementation with setPathParser().
       */
      function parsePath(subpath) {
        return subpath;
      }

      /**
       * @ngdoc function
       * @name setLoadFunction
       * @description
       * Sets the load() function that is used to load a single item with
       * an id specified.
       * @example
       ```
       getResourceType('thing').setLoadFunction(func);

       function func(descriptor) {
         return someApi.get(descriptor.id);
       }

       var loadPromise = resourceType.load({id: 'some-id'});
       ```
       */
      function setLoadFunction(func) {
        self.load = func;
        return self;
      }

      /**
       * True if the load function for this resource has been registered
       * @returns {boolean}
       */
      function isLoadFunctionSet() {
        return self.load !== defaultLoadFunction;
      }

      /**
       * @ngdoc function
       * @name load
       * @description
       * Load an item with the specified id. The implementation for this
       * function *must* be supplied with setLoadFunction()
       * @example
       ```
       var loadPromise = resourceType.load('some-id');
       ```
       */
      function defaultLoadFunction(spec) {
        $log.error('No load function defined for', typeCode, 'with spec', spec);
        return Promise.reject({data: {}});
      }

      /**
       * @ngdoc function
       * @name setPathGenerator
       * @description
       * Sets a function that is used generate paths.  Accepts the
       * resource-type-specific item object.
       *
       * The path generated here must be consumable by the path
       * parser supplied to setPathParser().
       *
       * The subpath returned should NOT have a leading slash.
       * @example
       ```
       resourceType.setPathGenerator(func);

       function func(item) {
         return 'load-balancer/' + item.balancerId
           + '/listener/' + item.id
       }
       ```
       */
      function setPathGenerator(func) {
        self.path = func;
        return self;
      }

      /**
       * @ngdoc function
       * @name path
       * @description
       * Generate a URL path for a resource item. The default implementation
       * returns the id of the passed in item, stringified.
       *
       * Replace the default implementation with setPathGenerator().
       * @example
       ```
       var path = resourceType.path({id: 12});
       ```
       */
      function path(item) {
        return '' + item.id;
      }

      /**
       * @ngdoc function
       * @name setSummaryTemplateUrl
       * @param url
       * @description
       * This sets the summaryTemplateUrl property on the resourceType.
       *
       * That URL points to a HTML fragment that renders a summary view of
       * a resource item. It can assume that an object named "item" exists
       * in its scope when rendered.
       */
      function setSummaryTemplateUrl(url) {
        self.summaryTemplateUrl = url;
        return self;
      }

      /**
       * @ngdoc function
       * @name setDefaultIndexUrl
       * @param url
       * @description
       * This sets the defaultIndexUrl property on the resourceType.
       *
       * That URL points to a index view that shows table view for the
       * resource type. The defaultIndexUrl will be used when details view
       * should redirect to index view (e.g. after deletion of the resource
       * itself) or should reset navigations (e.g. after refreshing details
       * view by browser).
       */
      function setDefaultIndexUrl(url) {
        self.defaultIndexUrl = url;
        return self;
      }

      /**
       * @ngdoc function
       * @name getDefaultIndexUrl
       * @param url
       * @description
       * This returns the defaultIndexUrl property on the resourceType.
       */
      function getDefaultIndexUrl() {
        return self.defaultIndexUrl;
      }

      /**
       * @ngdoc function
       * @name setItemNameFunction
       * @description
       * Set the itemName function.
       *
       */
      function setItemNameFunction(func) {
        self.itemName = func;
        return self;
      }

      /**
       * @ngdoc function
       * @name itemName
       * @description
       * Given an instance of a type (as returned by load()) this will generate
       * a human-readable name for that specific instance. The function used to
       * generate the name is set with setItemNameFunction().
       *
       */
      function itemName(item) {
        return item.name;
      }

      /**
       * @ngdoc function
       * @name getName
       * @description
       * Given a count, returns the appropriate name, handling multiples (i.e.
       * 'OS::Glance::Image' might return 'Image' or 'Images').
       *
       * The type's "names" property holds an array of the labels to be used
       * here which are passed to ngettext, so for example names could be
       * ['Image', 'Images']
       *
       * @example
       ```
       var resourceType = getResourceType('thing');
       resourceType.names = ['Thing', 'Things'];
       var singleName = resourceType.getName(1); // returns singular
       ```
       */
      function getName(count) {
        if (names) {
          return ngettext.apply(null, names.concat([count]));
        }
      }

      /**
       * @ngdoc function
       * @name setNames
       * @description
       * Takes in the untranslated singular/plural names used for display.
       * The "translated" parameter is to mark the strings for translation.
       * @example
       ```
       var resourceType = getResourceType('thing')
       .setNames('Thing', 'Things', ngettext('Thing', 'Things', 1));
       });

       ```
       */
      /* eslint-disable no-unused-vars */
      function setNames(singular, plural, translated) {
        names = [singular, plural];
        return self;
      }
      /* eslint-enable no-unused-vars */

      /**
       * @ngdoc function
       * @name label
       * @description
       * Returns a human-appropriate label for the given name.
       * The label is derived from the property definition from setProperty().
       *
       * @example
       ```
       var name = resourceType.label('disk_format'); // Yields 'Disk Format'
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
       * @name defaultNeedsFilterFirstFunction
       * @description
       * Returns a promise resolved to false to indicate that this feature
       * is not needed by default
       * @returns {Promise.<boolean>}
       */
      function defaultNeedsFilterFirstFunction() {
        return Promise.resolve(false);
      }

      /**
       * @ngdoc function
       * @param func
       * @description
       * Sets a custome needsFilterFirstFunction to the ResourceType object
       * such function must always return a promise and resolve that promise returning
       * a boolean value
       * @returns {ResourceType}
       *
       * @example
       ```
       function getFilterFirsSettingPromise(){
         return settingsService.getSetting('FILTER_DATA_FIRST',{'admin.images':false})
           .then(resolve);
         function resolve(result){
           return result['admin.images'];
         }
       }
       resourceType.setNeedsFilterFirstFunction(getFilterFirsSettingPromise)
       ```
       */
      function setNeedsFilterFirstFunction(func) {
        self.needsFilterFirstFunction = func;
        return self;
      }

    }

    var registry = {
      resourceTypes: {},
      defaultSummaryTemplateUrl: false,
      defaultDetailsTemplateUrl: false,
      getResourceType: getResourceType,
      getGlobalActions: getGlobalActions,
      setDefaultSummaryTemplateUrl: setDefaultSummaryTemplateUrl,
      getDefaultSummaryTemplateUrl: getDefaultSummaryTemplateUrl,
      setDefaultDetailsTemplateUrl: setDefaultDetailsTemplateUrl,
      getDefaultDetailsTemplateUrl: getDefaultDetailsTemplateUrl
    };

    function getDefaultSummaryTemplateUrl() {
      return registry.defaultSummaryTemplateUrl;
    }

    function setDefaultSummaryTemplateUrl(url) {
      registry.defaultSummaryTemplateUrl = url;
      return registry;
    }

    function getDefaultDetailsTemplateUrl() {
      return registry.defaultDetailsTemplateUrl;
    }

    /*
     * @ngdoc function
     * @name setDefaultDetailsTemplateUrl
     * @param {String} url - The URL for the template to be used
     * @description
     * The idea is that in the case that someone links to a details page for a
     * resource and there is no view registered, there can be a default view.
     * For example, if there's a generic property viewer, that could display
     * the resource.
     */
    function setDefaultDetailsTemplateUrl(url) {
      registry.defaultDetailsTemplateUrl = url;
      return registry;
    }

    /*
     * @ngdoc function
     * @name getGlobalActions
     * @description
     * This is a convenience function for retrieving all the global actions
     * across all the resource types.  This is valuable when a page wants to
     * display all actions that can be taken without having selected a resource
     * type, or otherwise needing to access all global actions.
     */
    function getGlobalActions() {
      var actions = [];
      angular.forEach(registry.resourceTypes, appendActions);
      return actions;

      function appendActions(type) {
        actions = actions.concat(type.globalActions);
      }
    }

    /*
     * @ngdoc function
     * @name getResourceType
     * @description
     * Retrieves all information about a resource type.  If the resource
     * type doesn't exist in the registry, this creates a new entry.
     *
     * @example
     ```
     var resourceType = registryService.getResourceType('OS::Glance::Image');
     ```
     */
    function getResourceType(typeCode) {
      if (!registry.resourceTypes.hasOwnProperty(typeCode)) {
        registry.resourceTypes[typeCode] = new ResourceType(typeCode);
      }
      return registry.resourceTypes[typeCode];
    }

    return registry;
  }

})();
