(function () {
  'use strict';
  angular.module('hz')
    .controller('hzMetadataWidgetCtrl', ['$scope', '$window', '$filter', function ($scope, $window, $filter) {

    //// Item class ////

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

    Item.prototype.fromNamespace = function(namespace) {
      this.label = namespace.display_name;
      this.description = namespace.description;

      if(namespace.objects) {
        angular.forEach(namespace.objects, function(object) {
          this.children.push(new Item(this).fromObject(object));
        }, this);
      }

      if(namespace.properties){
        angular.forEach(namespace.properties, function(property, key) {
          this.children.push(new Item(this).fromProperty(key, property));
        }, this);
      }

      this.sortChildren();

      return this;
    };

    Item.prototype.fromObject = function(object) {
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

    Item.prototype.fromProperty = function(name, property) {
      this.leaf = property || {};
      this.label = this.leaf.title || '';
      this.description = this.leaf.description || '';
      this.leaf.name = name;
      this.leaf.value = this.leaf.default || null;

      return this;
    };

    Item.prototype.customProperty = function(name) {
      this.fromProperty(name, {title: name});
      this.leaf.type = 'string';
      this.custom = true;

      return this;
    };

    Item.prototype.expand = function() {
      this.expanded = true;
      angular.forEach(this.children, function(child) {
        child.visible = true;
      }, this);
    };

    Item.prototype.collapse = function() {
      this.expanded = false;
      angular.forEach(this.children, function(child) {
        child.collapse();
        child.visible = false;
      }, this);
    };

    Item.prototype.sortChildren = function() {
      this.children.sort(function(a, b) {
        return a.label.localeCompare(b.label);
      });
    };

    Item.prototype.markAsAdded = function() {
      this.added = true;
      if(this.parent) {
        this.parent.addedCount += 1;
        if(this.parent.addedCount === this.parent.children.length) {
          this.parent.added = true;
        }
      }
      angular.forEach(this.children, function(item) {
        item.markAsAdded();
      }, this);
    };

    Item.prototype.unmarkAsAdded = function(caller) {
      this.added = false;
      if(this.parent) {
        this.parent.addedCount -= 1;
        this.parent.expand();
        this.parent.unmarkAsAdded(this);
      }
      if(!caller) { // prevent infinite recursion
        angular.forEach(this.children, function(item) {
          item.unmarkAsAdded();
        }, this);
      }
    };

    Item.prototype.path = function(path) {
      path = typeof path !== 'undefined' ? path : [];
      if(this.parent) this.parent.path(path);
      path.push(this.label);
      return path;
    };

    //// Private functions ////

    var filter = $filter('filter');

    function loadNamespaces(namespaces) {
      var items = [];

      angular.forEach(namespaces, function(namespace) {
        var item = new Item().fromNamespace(namespace);
        item.visible = true;
        items.push(item);
      });

      items.sort(function(a, b) {
        return a.label.localeCompare(b.label);
      });

      return items;
    }

    function flattenTree(tree, items) {
      items = typeof items !== 'undefined' ? items : [];

      angular.forEach(tree, function(item) {
        items.push(item);
        flattenTree(item.children, items);
      });

      return items;
    }

    function loadExisting(available, existing) {
      var itemsMapping = {};

      angular.forEach(available, function(item) {
        if(item.leaf && item.leaf.name in existing) {
          itemsMapping[item.leaf.name] = item;
        }
      });

      angular.forEach(existing, function(value, key) {
        var item = itemsMapping[key];
        if(typeof item === 'undefined') {
          item = new Item().customProperty(key);
          available.push(item);
        }
        switch (item.leaf.type) {
          case 'integer': item.leaf.value = parseInt(value); break;
          case 'number': item.leaf.value = parseFloat(value); break;
          case 'array': item.leaf.value = value.replace(/^<in> /, ''); break;
          default: item.leaf.value = value;
        }
        item.markAsAdded();
      });
    }

    //// Public functions ////

    $scope.onItemClick = function(e, item) {
      $scope.selected = item;
      if(!item.expanded) {
        item.expand();
      } else {
        item.collapse();
      }
    };

    $scope.onItemAdd = function(e, item) {
      $scope.selected = item;
      item.markAsAdded();
    };

    $scope.onItemDelete = function(e, item) {
      if(!item.custom) {
        $scope.selected = item;
        item.unmarkAsAdded();
      } else {
        $scope.selected = null;
        var i = $scope.flatTree.indexOf(item);
        if(i > -1) {
          $scope.flatTree.splice(i, 1);
        }
      }
    };

    $scope.onCustomItemAdd = function(e) {
      var item, name = $scope.customItem.value;
      if($scope.customItem.found.length > 0) {
        item = $scope.customItem.found[0];
        item.markAsAdded();
        $scope.selected = item;
      } else {
        item = new Item().customProperty(name);
        item.markAsAdded();
        $scope.selected = item;
        $scope.flatTree.push(item);
      }
      $scope.customItem.valid = false;
      $scope.customItem.value = '';
    };

    $scope.formatErrorMessage = function(item, error) {
      var _ = $window.gettext;
      if(error.min) return _('Min') + ' ' + item.leaf.minimum;
      if(error.max) return _('Max') + ' ' + item.leaf.maximum;
      if(error.minlength) return _('Min length') + ' ' + item.leaf.minLength;
      if(error.maxlength) return _('Max length') + ' ' + item.leaf.maxLength;
      if(error.pattern) {
        if(item.leaf.type === 'integer') return _('Integer required');
        else return _('Pattern mismatch');
      }
      if(error.required) {
        switch(item.leaf.type) {
          case 'integer': return _('Integer required');
          case 'number': return _('Decimal required');
          default: return _('Required');
        }
      }
    };

    $scope.saveMetadata = function () {
      var metadata = [];
      var added = filter($scope.flatTree, {'added': true, 'leaf': '!!'});
      angular.forEach(added, function(item) {
        metadata.push({
          key: item.leaf.name,
          value: (item.leaf.type == 'array' ? '<in> ' : '') + item.leaf.value
        });
      });
      $scope.metadata = JSON.stringify(metadata);
    };

    $scope.$watch('customItem.value', function() {
      $scope.customItem.found = filter(
          $scope.flatTree, {'leaf.name': $scope.customItem.value}, true
      );
      $scope.customItem.valid = $scope.customItem.value &&
          $scope.customItem.found.length === 0;
    });

    //// Private variables ////

    var tree = loadNamespaces($window.available_metadata.namespaces);

    //// Public variables ////

    $scope.flatTree = flattenTree(tree);
    $scope.decriptionText = '';
    $scope.metadata = '';
    $scope.selected = null;
    $scope.customItem = {
      value: '',
      focused: false,
      valid: false,
      found: []
    };

    loadExisting($scope.flatTree, $window.existing_metadata);

  }]);
}());
