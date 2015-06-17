/*
 * Copyright 2015 IBM Corp.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
(function() {
  'use strict';

  /**
   * @ngdoc overview
   * @name horizon.framework.widgets.toast
   * description
   *
   * # horizon.framework.widgets.toast
   *
   * The `horizon.framework.widgets.toast` module provides pop-up notifications to Horizon.
   * A toast is a short text message triggered by a user action to provide
   * real-time information. Toasts do not disrupt the page's behavior and
   * typically auto-expire and fade. Also, toasts do not accept any user
   * interaction.
   *
   *
   * | Components                                                               |
   * |--------------------------------------------------------------------------|
   * | {@link horizon.framework.widgets.toast.factory:toastService `toastService`}              |
   * | {@link horizon.framework.widgets.toast.directive:toast `toast`}                          |
   *
   */
  angular
    .module('horizon.framework.widgets.toast', []);

})();
