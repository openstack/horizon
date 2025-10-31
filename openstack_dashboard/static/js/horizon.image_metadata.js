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
(function () {
  'use strict';

  horizon.MetadataTree = class {
    constructor(root) {
      this.root = root;
      this.metadefs_init();
      this.namespaces_init();
      this.properties_init();
      this.objects_init();
      this.custom_init();
    }

    custom_init() {
      const input = this.root.querySelector('li.metadata-custom input');
      const button = this.root.querySelector('li.metadata-custom button');
      button.onclick = () => this.custom_click(input);
      input.oninput = () => this.custom_update(input);
    }

    custom_update(element) {
      const name = element.value;
      const button = this.root.querySelector('li.metadata-custom button');
      if (name) {
        button.removeAttribute('disabled');
      } else {
        button.setAttribute('disabled', 'disabled');
      }
    }

    custom_click(element) {
      const name = element.value;
      if (name) {
        this.property_add(name);
        this.metadefs_update();
        this.properties_update();
        this.objects_update();
        this.namespaces_update();
      }
      element.value = '';
      this.custom_update(element);
    }

    properties_init() {
      const properties = this.root.querySelectorAll('ul.metadata-properties li');
      for (let el of properties) {
        const element = el; // copy the value from the closure
        const button = element.querySelector('a.btn');
        button.onclick = () => this.property_remove(element);
      }
    }

    properties_update() {
      /* Rename forms and update the management form for the formset. */

    }

    property_remove(element) {
      /* Removes the property from the right hand side. */

      element.classList.add('metadata-used');
      for (let el of element.querySelectorAll('input, select')) {
        el.setAttribute('disabled', 'disabled');
      }
      this.metadefs_update();
      this.properties_update();
      this.objects_update();
      this.namespaces_update();
    }

    property_add(name) {
      /* Adds a new property to the right hand side. */
      if (name === 'image_id') {
        return; // This name is reserved.
      }
      const ul = this.root.querySelector('ul.metadata-properties');
      const prop = ul.querySelector(`li[data-name="${name}"]`);
      if (prop) {
        // This is a property from the namespace, make the field visible.
        prop.classList.remove('metadata-used');
        for (let el of prop.querySelectorAll('input, select')) {
          el.removeAttribute('disabled');
        }
      } else {
        // This is a custom property, add a field for it.
        const template = this.root.querySelector('template.metadata-property-template');
        const clone = document.importNode(template.content, true);
        const li = clone.querySelector('li');
        li.setAttribute('data-name', name);
        const label = li.querySelector('span.input-group-addon');
        label.setAttribute('title', name);
        label.textContent = name;
        const breadcrumb = li.querySelector('div.label');
        breadcrumb.textContent = name;
        const input = li.querySelector('input');
        input.setAttribute('name', name);
        const button = li.querySelector('a.btn');
        button.onclick = () => this.property_remove(li);
        ul.appendChild(li);
      }
      this.metadefs_update();
      this.properties_update();
      this.objects_update();
      this.namespaces_update();
    }

    namespaces_init() {
      const namespaces = this.root.querySelectorAll(
        'ul.metadata-metadefs li.metadata-namespace');
      for (let el of namespaces) {
        const element = el; // copy the value from the closure
        const button = element.querySelector('a.btn');
        button.onclick = (ev) => this.namespace_add(element, ev);
        element.onclick = () => this.namespace_click(element);
      }
      this.namespaces_update();
    }

    show_description(element) {
      const well = this.root.querySelector('div.well');
      const description = element.dataset.description;
      const title = element.dataset.title;
      const name = element.dataset.name;
      // We probably want some html escaping here?
      well.innerHTML = `<p><strong>${title}</strong> (${name})</p><p>${description}</p>`;
    }

    select_item(element) {
      this.root.querySelectorAll('ul.metadata-metadefs li').forEach(
        (el) => el.classList.remove('active'));
      element.classList.add('active');
    }

    namespace_click(element) {
      this.select_item(element);
      this.show_description(element);
      this.namespace_toggle(element);
    }

    namespace_toggle(element) {
      if (element.querySelector('span.fa-chevron-right')) {
        this.namespace_expand(element);
      } else {
        this.namespace_collapse(element);
      }
    }

    namespace_collapse(element) {
      /* Hide all items that belong to this namespace. */
      const namespace = element.dataset.name;
      const elements = this.root.querySelectorAll(
        `ul.metadata-metadefs li[data-parentnamespace="${namespace}"]`);
      for (let el of elements) {
        el.classList.add('metadata-collapsed');
      }
      const chevron = element.querySelector('span.fa');
      chevron.classList.add('fa-chevron-right');
      chevron.classList.remove('fa-chevron-down');
    }

    namespace_expand(element) {
      /* Show all items that belong to this namespace. */
      const name = element.dataset.name;
      const elements = this.root.querySelectorAll(
        `ul.metadata-metadefs li[data-parentnamespace="${name}"]`);
      for (let el of elements) {
        el.classList.remove('metadata-collapsed');
      }
      const chevron = element.querySelector('span.fa');
      chevron.classList.remove('fa-chevron-right');
      chevron.classList.add('fa-chevron-down');
    }

    namespace_add(element, ev) {
      /* Add all elements that belong to the namespace. */

      ev.preventDefault();
      const name = element.dataset.name;
      const metadefs = this.root.querySelectorAll(
        `ul.metadata-metadefs li.metadata-property[data-parentnamespace="${name}"]`);
      for (let element of metadefs) {
        this.property_add(element.dataset.name);
      }
      this.metadefs_update();
      this.properties_update();
      this.objects_update();
      this.namespaces_update();
    }

    namespaces_update() {
      /* Only show namespaces that are not empty. */

      const ul = this.root.querySelector('ul.metadata-metadefs');
      const namespaces = ul.querySelectorAll('li.metadata-namespace');
      for (let el of namespaces) {
        const name = el.dataset.name;
        const visible_children = ul.querySelectorAll(
          `li:not(.metadata-used)[data-parentnamespace="${name}"]`);
        if (visible_children.length === 0) {
          el.classList.add('metadata-used');
        } else {
          el.classList.remove('metadata-used');
        }
      }
    }

    objects_init() {
      const ul = this.root.querySelector('ul.metadata-metadefs');
      const objects = ul.querySelectorAll('li.metadata-object');
      for (let el of objects) {
        const element = el; // copy the value from the closure
        const button = element.querySelector('a.btn');
        button.onclick = (ev) => this.object_add(element, ev);
        element.onclick = () => this.object_click(element);
      }
      this.objects_update();
    }

    objects_update() {
      const ul = this.root.querySelector('ul.metadata-metadefs');
      const objects = ul.querySelectorAll('li.metadata-object');
      for (let el of objects) {
        const name = el.dataset.name;
        const namespace = el.dataset.parentnamespace;
        const visible_children = ul.querySelectorAll(
          `li:not(.metadata-used)[data-parentobject="${name}"][data-parentnamespace="${namespace}"]`);
        if (visible_children.length === 0) {
          el.classList.add('metadata-used');
        } else {
          el.classList.remove('metadata-used');
        }
      }
    }

    object_add(element, ev) {
      ev.preventDefault();
      const name = element.dataset.name;
      const namespace = element.dataset.parentnamespace;
      const metadefs = this.root.querySelectorAll(
        `ul.metadata-metadefs li[data-parentobject="${name}"][data-parentnamespace="${namespace}"]`);
      for (let element of metadefs) {
        this.property_add(element.dataset.name);
      }
      this.metadefs_update();
      this.properties_update();
      this.objects_update();
      this.namespaces_update();
    }

    object_expand(element) {
      const name = element.dataset.name;
      const namespace = element.dataset.parentnamespace;
      const elements = this.root.querySelectorAll(
        `ul.metadata-metadefs li[data-parentobject="${name}"][data-parentnamespace="${namespace}"]`);
      for (let el of elements) {
        el.classList.remove('metadata-objcollapsed');
      }
      const chevron = element.querySelector('span.fa');
      chevron.classList.remove('fa-chevron-right');
      chevron.classList.add('fa-chevron-down');
    }

    object_collapse(element) {
      const name = element.dataset.name;
      const namespace = element.dataset.parentnamespace;
      const elements = this.root.querySelectorAll(
        `ul.metadata-metadefs li[data-parentobject="${name}"][data-parentnamespace="${namespace}"]`);
      for (let el of elements) {
        el.classList.add('metadata-objcollapsed');
      }
      const chevron = element.querySelector('span.fa');
      chevron.classList.add('fa-chevron-right');
      chevron.classList.remove('fa-chevron-down');
    }

    object_toggle(element) {
      if (element.querySelector('span.fa-chevron-right')) {
        this.object_expand(element);
      } else {
        this.object_collapse(element);
      }
    }

    object_click(element) {
      this.select_item(element);
      this.show_description(element);
      this.object_toggle(element);
    }

    metadefs_init() {
      const metadefs = this.root.querySelectorAll(
        'ul.metadata-metadefs li.metadata-property');
      for (let el of metadefs) {
        const element = el; // copy the value from the closure
        const button = element.querySelector('a.btn');
        button.onclick = () => this.metadef_add(element);
        element.onclick = () => this.metadef_click(element);
      }
      this.metadefs_update();
    }

    metadefs_update() {
      /* Hide all properties on left hand side that are on the right. */

      const metadefs = this.root.querySelectorAll(
        'ul.metadata-metadefs li.metadata-property');
      let existing = [];
      this.root.querySelectorAll(
        'ul.metadata-properties li:not(.metadata-used)').forEach(
        (el) => existing.push(el.dataset.name));
      for (let element of metadefs) {
        if (existing.includes(element.dataset.name)) {
          element.classList.add('metadata-used');
        } else {
          element.classList.remove('metadata-used');
        }
      }
    }

    metadef_add(element) {
      this.property_add(element.dataset.name);
      this.metadefs_update();
      this.properties_update();
      this.objects_update();
      this.namespaces_update();
    }

    metadef_click(element) {
      this.show_description(element);
      this.select_item(element);
    }

    static connect() {
      for (let element of document.querySelectorAll('div.metadata-tree')) {
        if (element.dataset.initialized === "initialized") {
          continue;
        }
        new horizon.MetadataTree(element);
        element.dataset.initialized = "initialized";
      }
    }
  };
})();
