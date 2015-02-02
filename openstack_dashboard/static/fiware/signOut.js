var Fiware = Fiware || {};

Fiware.signOut = (function($, undefined) {
  var portals = {
    cloud: {
      name:      'Cloud',
      verb:      'GET',
      protocol:  'https',
      subdomain: 'cloud',
      path:      '/logout'
    },
    mashup: {
      name:      'Mashup',
      verb:      'GET',
      protocol:  'https',
      subdomain: 'mashup',
      path:      '/logout'
    },
    store: {
      name:      'Store',
      verb:      'GET',
      protocol:  'https',
      subdomain: 'store',
      path:      '/logout'
    },
    data: {
      name:      'Data',
      verb:      'GET',
      protocol:  'https',
      subdomain: 'data',
      path:      '/user/_logout'
    },
    account: {
      name:      'Account',
      verb:      'GET',
      protocol:  'https',
      subdomain: 'account',
      path:      '/auth/logout'
    }
  };

  var match = window.location.hostname.match(/\.(.*)/);
  var domain = match && match[1];

  // If domain exists, we are in production environment,
  // such as account.testbed.fi-ware.org
  var productionCall = function(currentPortal) {
    portalCalls = $.map(portals, function(portal) {
      url = portal.protocol + '://' + portal.subdomain + '.' + domain + portal.path;

      return $.ajax(url, {
        type: portal.verb,
        xhrFields: { withCredentials: true },
        error: function() { console.error("Error signing out " + portal.name); }
      });
    });

    deferredCall(portalCalls);
  };

  var deferredCall = function(calls) {
    $.when.apply($, calls).then(
      // success
      finish,
      // fail
      function() {
        if (calls.length === 1) {
          finish();
        } else {
          var unfinished = $.grep(calls, function(call) {
            return call.state() === "pending";
          });

          deferredCall(unfinished);
        }
      });
  };

  var finish = function() {
    // Use window.debugSignOut to debug
    if (window.debugSignOut === undefined) {
      window.location.replace('http://' + domain);
    }
  };

  // Development environment
  var developmentCall = function(currentPortal) {
    var url = 'http://' + window.location.host + portals[currentPortal].path;

    $.ajax(url, {
      type: portals[currentPortal].verb,
      success: function() {
        window.location.replace('http://' + window.location.host);
      }
    });
  };

  var call = function(currentPortal) {
      // productionCall(currentPortal);
      developmentCall(currentPortal);
  };

  return call;

})(jQuery);