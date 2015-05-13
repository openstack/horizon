(function () {
  'use strict';

  angular.module('hz.widget.metadata-tree')

  /**
   * @ngdoc service
   * @name hz.widget.metadata-tree.metadataTreeService
   */
  .factory('metadataTreeService', [function () {

    /**
     * Parse value into boolean
     *
     * @param {(string|boolean)} value
     * @returns {boolean}
     */
    function parseBool(value) {
      var value_type = typeof(value);

      if(value_type === 'boolean') {
        return value;
      }
      else if(value_type === 'string') {
        value = value.toLowerCase();

        if(value === 'true') {
          return true;
        }
        else if(value === 'false') {
          return false;
        }
      }

      return null;
    }

    /**
     * Construct a new property
     *
     * @class Property
     * @param {string} name
     * @param {Object} [json]
     *
     * @property {string} name Property key name
     * @property {string} title Property display name
     * @property {string} description Property description
     * @property {*} value Property value
     * @property {string} default Property default value
     * @property {string} type Property type
     * @property {boolean} readonly Property readonly state
     * @property {string[]} operators Property available operators when type='array'
     * @property {string} operator Property operator when type='array'
     */
    function Property(name, json) {
      this.name = name;
      this.title = name;
      this.description = '';
      this.value = null;
      this.default = null;
      this.type = 'string';
      this.readonly = false;
      this.operators = ['<in>'];
      angular.extend(this, json);
      this.operator = this.operators[0];
      this.setValue(this.default);
    }

    /**
     * Deserialize value and assign it to {@link Property#value}
     *
     * @param  {string} value
     */
    Property.prototype.setValue = function(value) {
      if(value === null) {
        this.value = this.type !== 'array' ? null : [];
        return;
      }

      switch (this.type) {
        case 'integer': this.value = parseInt(value); break;
        case 'number': this.value = parseFloat(value); break;
        case 'array':
          var data = /^(<.*?>) (.*)$/.exec(value);
          if(data) {
            this.operator = data[1];
            this.value = data[2].split(',');
          } break;
        case 'boolean': this.value = parseBool(value); break;
        default: this.value = value;
      }
    };

    /**
     * Serialize {@link Property#value} and returns it
     *
     * @returns {*}
     */
    Property.prototype.getValue = function() {
      switch (this.type) {
        case 'array': return this.operator + ' ' + this.value.join(',');
        default: return this.value;
      }
    };

    /**
     * Construct a new tree node
     *
     * @class Item
     * @param {Item} parent
     *
     * @property {Item} parent Item parent
     * @property {Item[]} children Item children
     * @property {boolean} visible Item visibility
     */
    function Item(parent) {
      // parent as property to prevent infinite recursion in angular filter
      Object.defineProperty(this, 'parent', {
        value: typeof parent !== 'undefined' ? parent : null
      });
      this.children = [];
      // Node properties
      this.visible = false;
      this.expanded = false;
      this.label = '';
      this.description = '';
      this.level = parent ? parent.level + 1 : 0;
      this.addedCount = 0;
      this.custom = false;
      // Leaf properties
      this.leaf = null;
      this.added = false;
    }

    /**
     * Load Item values and child Items from namespace definition
     *
     * @param {object} namespace Metadata namespace definition
     * @returns {Item}
     */
    Item.prototype.fromNamespace = function (namespace) {
      this.label = namespace.display_name;
      this.description = namespace.description;

      if(namespace.objects) {
        angular.forEach(namespace.objects, function (object) {
          this.children.push(new Item(this).fromObject(object));
        }, this);
      }

      if(namespace.properties) {
        angular.forEach(namespace.properties, function (property, key) {
          this.children.push(new Item(this).fromProperty(key, property));
        }, this);
      }

      this.sortChildren();

      return this;
    };

    /**
     * Load Item values and child Items from object definition
     *
     * @param {object} object Metadata object definition
     * @returns {Item}
     */
    Item.prototype.fromObject = function (object) {
      this.label = object.name;
      this.description = object.description;

      if(object.properties) {
        angular.forEach(object.properties, function (property, key) {
          this.children.push(new Item(this).fromProperty(key, property));
        }, this);
      }

      this.sortChildren();

      return this;
    };

    /**
     * Load Item values from property definition
     *
     * @param {string} name Property name
     * @param {object} property Metadata property definition
     * @returns {Item}
     */
    Item.prototype.fromProperty = function (name, property) {
      this.leaf = new Property(name, property);
      this.label = this.leaf.title;
      this.description = this.leaf.description;

      return this;
    };

    /**
     * Load Item values from property definition and mark as custom
     *
     * @param {string} name Property name
     * @param {object} property Metadata property definition
     * @returns {Item}
     */
    Item.prototype.customProperty = function (name, property) {
      this.fromProperty(name, property);
      this.custom = true;

      return this;
    };

    /**
     * Expand Item by marking all children as visible
     *
     * @param {boolean} deep Whether to recursively expand all child Items
     */
    Item.prototype.expand = function (deep) {
      this.expanded = true;
      angular.forEach(this.children, function (child) {
        if(deep) {
          child.expand(deep);
        }
        child.visible = true;
      }, this);
    };

    /**
     * Collapse Item by recursively unmarking all children as visible
     */
    Item.prototype.collapse = function () {
      this.expanded = false;
      angular.forEach(this.children, function (child) {
        child.collapse();
        child.visible = false;
      }, this);
    };

    /**
     * Sort children Items by label
     */
    Item.prototype.sortChildren = function () {
      this.children.sort(function (a, b) {
        return a.label.localeCompare(b.label);
      });
    };

    /**
     * Recursively mark Item and all children as added
     *
     * @param {=} caller Used internally to prevent infinite recursion
     */
    Item.prototype.markAsAdded = function (caller) {
      if(this.parent && !this.added) {
        this.parent.addedCount += 1;
        if(this.parent.addedCount === this.parent.children.length) {
          this.parent.markAsAdded(this);
        }
      }
      this.added = true;
      if(!caller) { // prevent infinite recursion
        angular.forEach(this.children, function (item) {
          item.markAsAdded();
        }, this);
      }
    };

    /**
     * Recursively unmark Item and all children as added
     *
     * @param {boolean=} expand Whether to expand parent of unmarked Item
     * @param {=} caller Used internally to prevent infinite recursion
     */
    Item.prototype.unmarkAsAdded = function (expand, caller) {
      if(this.parent) {
        if(expand) {
          this.parent.expand();
        }
        if(this.added) {
          this.parent.addedCount -= 1;
          this.parent.unmarkAsAdded(expand, this);
        }
      }
      this.added = false;
      if(!caller) { // prevent infinite recursion
        angular.forEach(this.children, function (item) {
          item.unmarkAsAdded(expand);
        }, this);
      }
    };

    /**
     * Returns list of Items from top-most parent to this Item
     *
     * @param {[]=} path Used internally
     * @returns {Item[]}
     */
    Item.prototype.path = function (path) {
      path = typeof path !== 'undefined' ? path : [];
      if(this.parent) {
        this.parent.path(path);
      }
      path.push(this);
      return path;
    };

    /**
     * Returns breadcrumb string for this Item
     *
     * @returns {string}
     */
    Item.prototype.breadcrumb = function () {
      return this.path().map(function (item) {
        return item.label;
      }).join(' › ');
    };

    /**
     * Parse string parameter into leaf value
     *
     * @param {string} value
     */
    Item.prototype.setLeafValue = function (value) {
      if(this.leaf) {
        this.leaf.setValue(value);
      }
    };

    /**
     * Serialize leaf value into string
     *
     * @returns {string}
     */
    Item.prototype.getLeafValue = function () {
      if(this.leaf) {
        return this.leaf.getValue();
      }
    };

    /**
     * Construct a new tree
     *
     * @class Tree
     * @param {object[]} available List of available namespaces
     * @param {object} existing Key-value pairs for existing metadata
     *
     * @property {Item[]} tree List available namespaces parsed into Item-s
     * @property {Item[]} flatTree List of Item-s flattened from tree structure
     * @property {Item} selected Selected Item
     */
    function Tree(available, existing) {
      this.tree = [];
      this.loadNamespaces(available);
      this.flatTree = this.flatten(this.tree);
      this.selected = null;
      this.loadExisting(existing);
    }

    /**
     * Load Item values and child Items from namespace definition
     *
     * @param {object[]} namespaces list of Metadata namespace definitions
     * @returns {Tree}
     */
    Tree.prototype.loadNamespaces = function (namespaces) {
      angular.forEach(namespaces, function (namespace) {
        var item = new Item().fromNamespace(namespace);
        item.visible = true;
        this.tree.push(item);
      }, this);

      this.tree.sort(function (a, b) {
        return a.label.localeCompare(b.label);
      });

      return this;
    };

    /**
     * Crete flat representation of branch
     *
     * @param {Item[]} branch List of Items to flatten
     * @param {[]=} items Used internally
     * @returns {Item[]}
     */
    Tree.prototype.flatten = function (branch, items) {
      items = typeof items !== 'undefined' ? items : [];

      angular.forEach(branch, function (item) {
        items.push(item);
        this.flatten(item.children, items);
      }, this);

      return items;
    };

    /**
     * Load Property.value for each value from existing and mark corresponding
     * Items as added. If no corresponding Item is found new Item is added and
     * marked as custom.
     *
     * @param {object} existing
     */
    Tree.prototype.loadExisting = function (existing) {
      var itemsMapping = {};

      angular.forEach(this.flatTree, function (item) {
        if(item.leaf && item.leaf.name in existing) {
          itemsMapping[item.leaf.name] = item;
        }
      });

      angular.forEach(existing, function (value, key) {
        var item = itemsMapping[key];
        if(typeof item === 'undefined') {
          item = new Item().customProperty(key);
          this.flatTree.push(item);
        }
        item.setLeafValue(value);
        item.markAsAdded();
      }, this);
    };

    /**
     * Returns key-value mapping of leaf Items that was marked as added
     *
     * @returns {object}
     */
    Tree.prototype.getExisting = function () {
      var existing = {};
      angular.forEach(this.flatTree, function(item) {
        if(item.added && item.leaf) {
          existing[item.leaf.name] = item.getLeafValue();
        }
      });
      return existing;
    };

    /**
     * Selects item and expands / collapses it
     *
     * @param {Item} item
     */
    Tree.prototype.select = function (item) {
      this.selected = item;
      if(!item.expanded) {
        item.expand();
      } else {
        item.collapse();
      }
    };

    /**
     * Selects item and marks it as added
     *
     * @param {Item} item
     */
    Tree.prototype.markAsAdded = function (item) {
      this.selected = item;
      item.markAsAdded();
    };

    /**
     * Selects item, unmarks it as added and expands it's parent
     *
     * @param {Item} item
     */
    Tree.prototype.unmarkAsAdded = function (item) {
      if(!item.custom) {
        this.selected = item;
        item.unmarkAsAdded(true);
      } else {
        this.selected = null;
        var i = this.flatTree.indexOf(item);
        if(i > -1) {
          this.flatTree.splice(i, 1);
        }
      }
    };

    /**
     * Adds new Item, selects it and marks it as custom and added
     *
     * @param {string} name Name of leaf
     */
    Tree.prototype.addCustom = function (name) {
      var item = new Item().customProperty(name);
      item.markAsAdded();
      this.flatTree.push(item);
      this.selected = item;
    };

    return {
      Item: Item,
      Property: Property,
      Tree: Tree
    };
  }]);
}());
