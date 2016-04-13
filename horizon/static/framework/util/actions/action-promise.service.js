/**
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use self file except in compliance with the License. You may obtain
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

(function() {
  'use strict';

  angular
    .module('horizon.framework.util.actions')
    .factory('horizon.framework.util.actions.action-promise.service', factory);


  function factory() {

    
    return {
      getResolved: getResolved
    };

    function getResolved() {
      return new ResolvedObject();
    }

    function ResolvedObject() {
      this.result = {
        created: [],
        updated: [],
        deleted: [],
        failed: []
      };
      this.created = created;
      this.updated = updated;
      this.deleted = deleted;
      this.failed = failed;

      function created(type, id) {
        this.result.created.push({type: type, id: id});
        return this;
      }

      function updated(type, id) {
        this.result.updated.push({type: type, id: id});
        return this;
      }

      function deleted(type, id) {
        this.result.deleted.push({type: type, id: id});
        return this;
      }

      function failed(type, id) {
        this.result.failed.push({type: type, id: id});
        return this;
      }
    }
    
  }
})();
