/* global Hogan */
/* Namespace for core functionality related to Network Topology. */

function Network(data) {
  for (var key in data) {
    if ({}.hasOwnProperty.call(data, key)) {
      this[key] = data[key];
    }
  }
  this.iconType = 'text';
  this.icon = '\uf0c2'; // Cloud
  this.collapsed = false;
  this.type = 'network';
  this.instances = 0;
}

function ExternalNetwork(data) {
  for (var key in data) {
    if ({}.hasOwnProperty.call(data, key)) {
      this[key] = data[key];
    }
  }
  this.collapsed = false;
  this.iconType = 'text';
  this.icon = '\uf0ac'; // Globe
  this.instances = 0;
}

function Router(data) {
  for (var key in data) {
    if ({}.hasOwnProperty.call(data, key)) {
      this[key] = data[key];
    }
  }
  this.iconType = 'path';
  this.svg = 'router';
  this.networks = [];
  this.ports = [];
  this.type = 'router';
}

function Server(data) {
  for (var key in data) {
    if ({}.hasOwnProperty.call(data, key)) {
      this[key] = data[key];
    }
  }
  this.iconType = 'text';
  this.icon = '\uf108'; // Server
  this.networks = [];
  this.type = 'instance';
  this.ip_addresses = [];
}

horizon.network_topology = {
  model: null,
  fa_globe_glyph: '\uf0ac',
  fa_globe_glyph_width: 15,
  svg:'#topology_canvas',
  nodes: [],
  links: [],
  data: [],
  zoom: d3.behavior.zoom(),
  data_loaded: false,
  svg_container:'#topologyCanvasContainer',
  post_messages:'#topologyMessages',
  balloonTmpl : null,
  balloon_deviceTmpl : null,
  balloon_portTmpl : null,
  balloon_netTmpl : null,
  balloon_instanceTmpl : null,
  network_index: {},
  balloonID:null,
  reload_duration: 10000,
  network_height : 0,
  previous_message : null,
  deleting_device : null,

  init:function() {
    var self = this;
    angular.element(self.svg_container).spin(horizon.conf.spinner_options.modal);
    if (angular.element('#networktopology').length === 0) {
      return;
    }

    self.data = {};
    self.data.networks = {};
    self.data.routers = {};
    self.data.servers = {};
    self.data.ports = {};

    // Setup balloon popups
    self.balloonTmpl = Hogan.compile(angular.element('#balloon_container').html());
    self.balloon_deviceTmpl = Hogan.compile(angular.element('#balloon_device').html());
    self.balloon_portTmpl = Hogan.compile(angular.element('#balloon_port').html());
    self.balloon_netTmpl = Hogan.compile(angular.element('#balloon_net').html());
    self.balloon_instanceTmpl = Hogan.compile(angular.element('#balloon_instance').html());

    angular.element(document)
      .on('click', 'a.closeTopologyBalloon', function(e) {
        e.preventDefault();
        self.delete_balloon();
      })
      .on('click', '.topologyBalloon', function(e) {
        e.stopPropagation();
      })
      .on('click', 'a.vnc_window', function(e) {
        e.preventDefault();
        var vncWindow = window.open(angular.element(this).attr('href'), vncWindow,
                                     'width=760,height=560');
        self.delete_balloon();
      });

    angular.element('#toggle_labels').click(function() {
      if (angular.element('.nodeLabel').css('display') == 'none') {
        angular.element('.nodeLabel').show();
        horizon.cookies.put('show_labels', true);
      } else {
        angular.element('.nodeLabel').hide();
        horizon.cookies.put('show_labels', false);
      }
    });

    angular.element('#toggle_networks').click(function() {
      for (var n in self.nodes) {
        if ({}.hasOwnProperty.call(self.nodes, n)) {
          if (self.nodes[n].data instanceof Network || self.nodes[n].data instanceof ExternalNetwork) {
            self.collapse_network(self.nodes[n]);
          }
          if (horizon.cookies.get('show_labels')) {
            angular.element('.nodeLabel').show();
          }
        }
      }
      var current = horizon.cookies.get('are_networks_collapsed');
      horizon.cookies.put('are_networks_collapsed', !current);
    });

    angular.element(window).on('message', function(e) {
        var message = angular.element.parseJSON(e.originalEvent.data);
        if (self.previous_message !== message.message) {
          horizon.alert(message.type, message.message);
          horizon.autoDismissAlerts();
          self.previous_message = message.message;
          self.delete_post_message(message.iframe_id);
          if (message.type == 'success' && self.deleting_device) {
            self.remove_node_on_delete();
          }
          self.retrieve_network_info();
          setTimeout(function() {
            self.previous_message = null;
          },10000);
        }
      });

    angular.element('#topologyCanvasContainer').spin(horizon.conf.spinner_options.modal);
    self.create_vis();
    self.loading();
    self.force_direction(0.05,70,-700);
    self.retrieve_network_info(true);
  },

  // Get the json data about the current deployment
  retrieve_network_info: function(force_start) {
    var self = this;
    if (angular.element('#networktopology').length === 0) {
      return;
    }
    angular.element.getJSON(
      angular.element('#networktopology').data('networktopology') + '?' + angular.element.now(),
      function(data) {
        self.data_loaded = true;
        self.load_topology(data);
        if (force_start) {
          var i = 0;
          self.force.start();
          while (i <= 100) {
            self.force.tick();
            i++;
          }
        }
        setTimeout(function() {
          self.retrieve_network_info();
        }, self.reload_duration);
      }
    );
  },

  // Load config from cookie
  load_config: function() {
    var labels = horizon.cookies.get('show_labels');
    var networks = horizon.cookies.get('are_networks_collapsed');
    if (labels) {
      angular.element('.nodeLabel').show();
      angular.element('#toggle_labels').addClass('active');
    }
    if (networks) {
      for (var n in this.nodes) {
        if ({}.hasOwnProperty.call(this.nodes, n)) {
          this.collapse_network(this.nodes[n], true);
        }
      }
      angular.element('#toggle_networks').addClass('active');
    }
  },

  getScreenCoords: function(x, y) {
    var self = this;
    if (self.translate) {
      var xn = self.translate[0] + x * self.zoom.scale();
      var yn = self.translate[1] + y * self.zoom.scale();
      return { x: xn, y: yn };
    } else {
      return { x: x, y: y };
    }
  },

  // Setup the main visualisation
  create_vis: function() {
    var self = this;
    angular.element('#topologyCanvasContainer').html('');

    // Main svg
    self.outer_group = d3.select('#topologyCanvasContainer').append('svg')
      .attr('width', '100%')
      .attr('height', angular.element(document).height() - 200 + "px")
      .attr('pointer-events', 'all')
      .append('g')
      .call(self.zoom
        .scaleExtent([0.1,1.5])
        .on('zoom', function() {
            self.delete_balloon();
            self.vis.attr('transform', 'translate(' + d3.event.translate + ')scale(' +
              self.zoom.scale() + ')');
            self.translate = d3.event.translate;
          })
        )
      .on('dblclick.zoom', null);

    // Background for capturing mouse events
    self.outer_group.append('rect')
      .attr('width', '100%')
      .attr('height', '100%')
      .attr('fill', 'white')
      .on('click', function() {
        self.delete_balloon();
      });

    // svg wrapper for nodes to sit on
    self.vis = self.outer_group.append('g');
  },

  loading: function() {
    var self = this;
    var load_text = self.vis.append('text')
        .style('fill', 'black')
        .style('font-size', '40')
        .attr('x', '50%')
        .attr('y', '50%')
        .text('');
    var counter = 0;
    var timer = setInterval(function() {
      var i;
      var str = '';
      for (i = 0; i <= counter; i++) {
        str += '.';
      }
      load_text.text(str);
      if (counter >= 9) {
        counter = 0;
      } else {
        counter++;
      }
      if (self.data_loaded) {
        clearInterval(timer);
        load_text.remove();
      }
    }, 100);
  },

  // Calculate the hulls that surround networks
  convex_hulls: function(nodes) {
    var net, _i, _len, _ref, _h, i;
    var hulls = {};
    var networkids = {};
    var k = 0;
    var offset = 40;

    while ( k < nodes.length) {
      var n = nodes[k];
      if (n.data !== undefined) {
        if (n.data instanceof Server) {
          _ref = n.data.networks;
          for (_i = 0, _len = _ref.length; _i < _len; _i++) {
            net = _ref[_i];
            if (net instanceof Network) {
              _h = hulls[net.id] || (hulls[net.id] = []);
              _h.push([n.x - offset, n.y - offset]);
              _h.push([n.x - offset, n.y + offset]);
              _h.push([n.x + offset, n.y - offset]);
              _h.push([n.x + offset, n.y + offset]);
            }
          }
        } else if (n.data instanceof Network) {
          net = n.data;
          networkids[net.id] = n;
          _h = hulls[net.id] || (hulls[net.id] = []);
          _h.push([n.x - offset, n.y - offset]);
          _h.push([n.x - offset, n.y + offset]);
          _h.push([n.x + offset, n.y - offset]);
          _h.push([n.x + offset, n.y + offset]);

        }
      }
      ++k;
    }
    var hullset = [];
    for (i in hulls) {
      if ({}.hasOwnProperty.call(hulls, i)) {
        hullset.push({group: i, network: networkids[i], path: d3.geom.hull(hulls[i])});
      }
    }

    return hullset;
  },

  // Setup the force direction
  force_direction: function(grav, dist, ch) {
    var self = this;

    angular.element('[data-toggle="tooltip"]').tooltip({container: 'body'});
    self.curve = d3.svg.line()
      .interpolate('cardinal-closed')
      .tension(0.85);
    self.fill = d3.scale.category10();

    self.force = d3.layout.force()
      .gravity(grav)
      .linkDistance(function(d) {
        if (d.source.data instanceof Server || d.target.data instanceof Server) {
          if (d.source.data.networks) {
            return (dist * d.source.data.networks.length) + (5 * d.target.data.instances) + 20;
          } else if (d.target.data.networks) {
            return (dist * d.target.data.networks.length) + (5 * d.source.data.instances) + 20;
          }
        } else if (d.source.data instanceof Router || d.target.data instanceof Router) {
          if (d.source.data.networks) {
            if (d.source.data.networks.length === 0) {
              return dist + 20;
            } else if (d.target.data.instances) {
              return dist * d.source.data.networks.length + (10 * d.target.data.instances) + 20;
            }
            return dist * d.source.data.networks.length + 20;
          } else if (d.target.data.networks) {
            if (d.target.data.networks.length === 0) {
              return dist + 20;
            } else if (d.source.data.instances) {
              return dist * d.target.data.networks.length + (10 * d.source.data.instances) + 20;
            }
            return dist * d.source.data.networks.length + 20;
          }
        } else {
          return dist;
        }
      })
      .charge(ch)
      .size([angular.element('#topologyCanvasContainer').width(),
             angular.element('#topologyCanvasContainer').height()])
      .nodes(self.nodes)
      .links(self.links)
      .on('tick', function() {
        self.vis.selectAll('g.node')
          .attr('transform', function(d) {
            return 'translate(' + d.x + ',' + d.y + ')';
          });

        self.vis.selectAll('line.link')
          .attr('x1', function(d) { return d.source.x; })
          .attr('y1', function(d) { return d.source.y; })
          .attr('x2', function(d) { return d.target.x; })
          .attr('y2', function(d) { return d.target.y; });

        self.vis.selectAll('path.hulls')
          .data(self.convex_hulls(self.vis.selectAll('g.node').data()))
            .attr('d', function(d) {
              return self.curve(d.path);
            })
          .enter().insert('path', 'g')
            .attr('class', 'hulls')
            .style('fill', function(d) {
              return self.fill(d.group);
            })
            .style('stroke', function(d) {
              return self.fill(d.group);
            })
            .style('stroke-linejoin', 'round')
            .style('stroke-width', 10)
            .style('opacity', 0.2);
      });
  },

  // Create a new node
  new_node: function(data, x, y) {
    var self = this;
    data = {data: data};
    if (x && y) {
      data.x = x;
      data.y = y;
    }
    self.nodes.push(data);

    var node = self.vis.selectAll('g.node').data(self.nodes);
    var nodeEnter = node.enter().append('g')
      .attr('class', 'node')
      .style('fill', 'white')
      .call(self.force.drag);

    nodeEnter.append('circle')
      .attr('class', 'frame')
      .attr('r', function(d) {
        switch (Object.getPrototypeOf(d.data)) {
          case ExternalNetwork.prototype:
            return 35;
          case Network.prototype:
            return 30;
          case Router.prototype:
            return 25;
          case Server.prototype:
            return 20;
        }
      })
      .style('fill', 'white')
      .style('stroke', 'black')
      .style('stroke-width', 3);

    switch ( data.data.iconType ) {
      case 'text':
        nodeEnter.append('text')
          .style('fill', 'black')
          .style('font', '20px FontAwesome')
          .attr('text-anchor', 'middle')
          .attr('dominant-baseline', 'central')
          .text(function(d) { return d.data.icon; })
          .attr('transform', function(d) {
            switch (Object.getPrototypeOf(d.data)) {
              case ExternalNetwork.prototype:
                return 'scale(2.5)';
              case Network.prototype:
                return 'scale(1.5)';
              case Server.prototype:
                return 'scale(1)';
            }
          });
        break;
      case 'path':
        nodeEnter.append('path')
          .attr('class', 'svgpath')
          .style('fill', 'black')
          .attr('d', function(d) { return self.svgs(d.data.svg); })
          .attr('transform', function() {
            return 'scale(1.2)translate(-16,-15)';
          });
        break;
    }

    nodeEnter.append('text')
      .attr('class', 'nodeLabel')
      .style('display',function() {
        var labels = horizon.cookies.get('topology_labels');
        if (labels) {
          return 'inline';
        } else {
          return 'none';
        }
      })
      .style('fill','black')
      .text(function(d) {
        return d.data.name;
      })
      .attr('transform', function(d) {
        switch (Object.getPrototypeOf(d.data)) {
          case ExternalNetwork.prototype:
            return 'translate(40,3)';
          case Network.prototype:
            return 'translate(35,3)';
          case Router.prototype:
            return 'translate(30,3)';
          case Server.prototype:
            return 'translate(25,3)';
        }
      });

    if (data.data instanceof Network || data.data instanceof ExternalNetwork) {
      nodeEnter.append('svg:text')
        .attr('class','vmCount')
        .style('fill', 'black')
        .style('font-size','20')
        .text('')
        .attr('transform', 'translate(26,38)');
    }

    nodeEnter.on('click', function(d) {
      self.show_balloon(d.data, d, angular.element(this));
    });

    // Highlight the links for currently selected node
    nodeEnter.on('mouseover', function(d) {
      self.vis.selectAll('line.link').filter(function(z) {
        if (z.source === d || z.target === d) {
          return true;
        } else {
          return false;
        }
      }).style('stroke-width', '3px');
    });

    // Remove the highlight on the links
    nodeEnter.on('mouseout', function() {
      self.vis.selectAll('line.link').style('stroke-width','1px');
    });
  },

  collapse_network: function(d, only_collapse) {
    var self = this;
    var server, vm;

    var filterNode = function(obj) {
      return function(d) {
        return obj == d.data;
      };
    };

    if (!d.data.collapsed) {
      var vmCount = 0;
      for (vm in self.data.servers) {
        if (self.data.servers[vm] !== undefined) {
          if (self.data.servers[vm].networks.length == 1) {
            if (self.data.servers[vm].networks[0].id == d.data.id) {
              vmCount += 1;
              self.removeNode(self.data.servers[vm]);
            }
          }
        }
      }
      d.data.collapsed = true;
      if (vmCount > 0) {
        self.vis.selectAll('.vmCount').filter(filterNode(d.data))[0][0].textContent = vmCount;
      }
    } else if (!only_collapse) {
      for (server in self.data.servers) {
        if ({}.hasOwnProperty.call(self.data.servers, server)) {
          var _vm = self.data.servers[server];
          if (_vm !== undefined) {
            if (_vm.networks.length === 1) {
              if (_vm.networks[0].id == d.data.id) {
                self.new_node(_vm, d.x, d.y);
                self.new_link(self.find_by_id(_vm.id), self.find_by_id(d.data.id));
                self.force.start();
              }
            }
          }
        }
      }
      d.data.collapsed = false;
      self.vis.selectAll('.vmCount').filter(filterNode(d.data))[0][0].textContent = '';
      var i = 0;
      while (i <= 100) {
        self.force.tick();
        i++;
      }
    }
  },

  new_link: function(source, target) {
    var self = this;
    self.links.push({source: source, target: target});
    var line = self.vis.selectAll('line.link').data(self.links);
    line.enter().insert('line', 'g.node')
      .attr('class', 'link')
      .attr('x1', function(d) { return d.source.x; })
      .attr('y1', function(d) { return d.source.y; })
      .attr('x2', function(d) { return d.target.x; })
      .attr('y2', function(d) { return d.target.y; })
      .style('stroke', 'black')
      .style('stroke-width', 2);
  },

  find_by_id: function(id) {
    var self = this;
    var obj, _i, _len, _ref;
    _ref = self.vis.selectAll('g.node').data();
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      obj = _ref[_i];
      if (obj.data.id == id) {
        return obj;
      }
    }
    return undefined;
  },

  already_in_graph: function(data, node) {
    // Check for gateway that may not have unique id
    if (data == this.data.ports) {
      for (var p in data) {
        if (JSON.stringify(data[p]) == JSON.stringify(node)) {
          return true;
        }
      }
      return false;
    }
    // All other node types have UUIDs
    for (var n in data) {
      if (n == node.id) {
        return true;
      }
    }
    return false;
  },

  load_topology: function(data) {
    var self = this;
    var net, _i, _netlen, _netref, rou, _j, _roulen, _rouref, port, _l, _portlen, _portref,
        ser, _k, _serlen, _serref, obj, vmCount;
    var change = false;
    var filterNode = function(obj) {
      return function(d) {
        return obj == d.data;
      };
    };

    // Networks
    _netref = data.networks;
    for (_i = 0, _netlen = _netref.length; _i < _netlen; _i++) {
      net = _netref[_i];
      var network = null;
      if (net['router:external'] === true) {
        network = new ExternalNetwork(net);
      } else {
        network = new Network(net);
      }

      if (!self.already_in_graph(self.data.networks, network)) {
        self.new_node(network);
        change = true;
      } else {
        obj = self.find_by_id(network.id);
        if (obj) {
          network.collapsed = obj.data.collapsed;
          network.instances = obj.data.instances;
          obj.data = network;
        }
      }
      self.data.networks[network.id] = network;
    }

    // Routers
    _rouref = data.routers;
    for (_j = 0, _roulen = _rouref.length; _j < _roulen; _j++) {
      rou = _rouref[_j];
      var router = new Router(rou);
      if (!self.already_in_graph(self.data.routers, router)) {
        self.new_node(router);
        change = true;
      } else {
        obj = self.find_by_id(router.id);
        if (obj) {
          // Keep networks list
          router.networks = obj.data.networks;
          // Keep ports list
          router.ports = obj.data.ports;
          obj.data = router;
        }
      }
      self.data.routers[router.id] = router;
    }

    // Servers
    _serref = data.servers;
    for (_k = 0, _serlen = _serref.length; _k < _serlen; _k++) {
      ser = _serref[_k];
      var server = new Server(ser);
      if (!self.already_in_graph(self.data.servers, server)) {
        self.new_node(server);
        change = true;
      } else {
        obj = self.find_by_id(server.id);
        if (obj) {
          // Keep networks list
          server.networks = obj.data.networks;
          // Keep ip address list
          server.ip_addresses = obj.data.ip_addresses;
          obj.data = server;
        } else if (self.data.servers[server.id] !== undefined) {
          // This is used when servers are hidden because the network is
          // collapsed
            server.networks = self.data.servers[server.id].networks;
            server.ip_addresses = self.data.servers[server.id].ip_addresses;
        }
      }
      self.data.servers[server.id] = server;
    }

    // Ports
    _portref = data.ports;
    for (_l = 0, _portlen = _portref.length; _l < _portlen; _l++) {
      port = _portref[_l];
      if (!self.already_in_graph(self.data.ports, port)) {
        var device = self.find_by_id(port.device_id);
        var _network = self.find_by_id(port.network_id);
        if (angular.isDefined(device) && angular.isDefined(_network)) {
          if (port.device_owner == 'compute:nova' || port.device_owner == 'compute:None') {
            _network.data.instances++;
            device.data.networks.push(_network.data);
            if (port.fixed_ips) {
              for(var ip in port.fixed_ips) {
                device.data.ip_addresses.push(port.fixed_ips[ip]);
              }
            }
            // Remove the recently added node if connected to a network which is
            // currently collapsed
            if (_network.data.collapsed) {
              if (device.data.networks.length == 1) {
                self.data.servers[device.data.id].networks = device.data.networks;
                self.data.servers[device.data.id].ip_addresses = device.data.ip_addresses;
                self.removeNode(self.data.servers[port.device_id]);
                vmCount = Number(self.vis.selectAll('.vmCount').filter(filterNode(_network.data))[0][0].textContent);
                self.vis.selectAll('.vmCount').filter(filterNode(_network.data))[0][0].textContent = vmCount + 1;
                continue;
              }
            }
          } else if (port.device_owner == 'network:router_interface') {
            device.data.networks.push(_network.data);
            device.data.ports.push(port);
          } else if (device.data.ports) {
            device.data.ports.push(port);
          }
          self.new_link(self.find_by_id(port.device_id), self.find_by_id(port.network_id));
          change = true;
        } else if (angular.isDefined(_network) && port.device_owner == 'compute:nova') {
          // Need to add a previously hidden node to the graph because it is
          // connected to more than 1 network
          if (_network.data.collapsed) {
            server = self.data.servers[port.device_id];
            server.networks.push(_network.data);
            if (port.fixed_ips) {
              for(var ip in port.fixed_ips) {
                server.ip_addresses.push(port.fixed_ips[ip]);
              }
            }
            self.new_node(server);
            // decrease collapsed vm count on network
            vmCount = Number(self.vis.selectAll('.vmCount').filter(filterNode(server.networks[0]))[0][0].textContent);
            if (vmCount == 1) {
              self.vis.selectAll('.vmCount').filter(filterNode(server.networks[0]))[0][0].textContent = '';
            } else {
              self.vis.selectAll('.vmCount').filter(filterNode(server.networks[0]))[0][0].textContent = vmCount - 1;
            }
            // Add back in first network link
            self.new_link(self.find_by_id(port.device_id), self.find_by_id(server.networks[0].id));
            // Add new link
            self.new_link(self.find_by_id(port.device_id), self.find_by_id(port.network_id));
            change = true;
          }
        }
      }
      self.data.ports[port.id+port.device_id+port.network_id] = port;
    }
    if (change) {
        self.force.start();
    }
    self.load_config();
  },

  removeNode: function(obj) {
    var filterNetwork, filterNode, n, node, _i, _len, _ref;
    _ref = this.nodes;
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      n = _ref[_i];
      if (n.data === obj) {
        node = n;
        break;
      }
    }
    if (node) {
      this.nodes.splice(this.nodes.indexOf(node), 1);
      filterNode = function(obj) {
        return function(d) {
          return obj === d.data;
        };
      };
      filterNetwork = function(obj) {
        return function(d) {
          return obj === d.network.data;
        };
      };
      if (obj instanceof Network) {
        this.vis.selectAll('.hulls').filter(filterNetwork(obj)).remove();
      }
      this.vis.selectAll('g.node').filter(filterNode(obj)).remove();
      return this.removeNodesLinks(obj);
    }
  },

  removeNodesLinks: function(node) {
    var l, linksToRemove, _i, _j, _len, _len1, _ref;
    linksToRemove = [];
    _ref = this.links;
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      l = _ref[_i];
      if (l.source.data === node) {
        linksToRemove.push(l);
      } else if (l.target.data === node) {
        linksToRemove.push(l);
      }
    }
    for (_j = 0, _len1 = linksToRemove.length; _j < _len1; _j++) {
      l = linksToRemove[_j];
      this.removeLink(l);
    }
    return this.force.resume();
  },

  removeLink: function(link) {
    var i, index, l, _i, _len, _ref;
    index = -1;
    _ref = this.links;
    for (i = _i = 0, _len = _ref.length; _i < _len; i = ++_i) {
      l = _ref[i];
      if (l === link) {
        index = i;
        break;
      }
    }
    if (index !== -1) {
      this.links.splice(index, 1);
    }
    return this.vis.selectAll('line.link').data(this.links).exit().remove();
  },

  delete_device: function(type, deviceId) {
    var self = this;
    var message = {id:deviceId};
    self.post_message(deviceId,type,message);
    self.deleting_device = {type: type, deviceId: deviceId};
  },

  remove_node_on_delete: function () {
    var self = this;
    var type = self.deleting_device.type;
    var deviceId = self.deleting_device.deviceId;
    switch (type) {
      case 'router':
        self.removeNode(self.data.routers[deviceId]);
        break;
      case 'instance':
        self.removeNode(self.data.servers[deviceId]);
        this.data.servers[deviceId] = undefined;
        break;
      case 'network':
        self.removeNode(self.data.networks[deviceId]);
        break;
    }
    self.delete_balloon();
  },

  delete_port: function(routerId, portId, networkId) {
    var self = this;
    var message = {id:portId};
    if (routerId) {
      self.post_message(portId, 'router/' + routerId + '/', message);
      for (var l in self.links) {
        var data = null;
        if(self.links[l].source.data.id == routerId && self.links[l].target.data.id == networkId) {
          data = self.links[l].source.data;
        } else if (self.links[l].target.data.id == routerId && self.links[l].source.data.id == networkId) {
          data = self.links[l].target.data;
        }

        if (data) {
          for (var p in data.ports) {
            if ((data.ports[p].id == portId) && (data.ports[p].network_id == networkId)) {
              self.removeLink(self.links[l]);
              // Update Router to remove deleted port
              var router = self.find_by_id(routerId);
              router.data.ports.splice(router.data.ports.indexOf(data.ports[p]), 1);
              self.force.start();
              return;
            }
          }
        }
      }
    } else {
      self.post_message(portId, 'network/' + networkId + '/', message);
    }
  },

  show_balloon: function(d,d2,element) {
    var self = this;
    var balloonTmpl = self.balloonTmpl;
    var deviceTmpl = self.balloon_deviceTmpl;
    var portTmpl = self.balloon_portTmpl;
    var netTmpl = self.balloon_netTmpl;
    var instanceTmpl = self.balloon_instanceTmpl;
    var balloonID = 'bl_' + d.id;
    var ports = [];
    var subnets = [];
    if (self.balloonID) {
      if (self.balloonID == balloonID) {
        self.delete_balloon();
        return;
      }
      self.delete_balloon();
    }
    self.force.stop();
    if (d.hasOwnProperty('ports')) {
      angular.element.each(d.ports, function(i, port) {
        var object = {};
        object.id = port.id;
        object.router_id = port.device_id;
        object.url = port.url;
        object.port_status = port.status;
        object.port_status_css = (port.status === 'ACTIVE') ? 'active' : 'down';
        var ipAddress = '';
        try {
          for (var ip in port.fixed_ips) {
            ipAddress += port.fixed_ips[ip].ip_address + ' ';
          }
        }catch(e) {
          ipAddress = gettext('None');
        }
        var deviceOwner = '';
        try {
          deviceOwner = port.device_owner.replace('network:','');
        }catch(e) {
          deviceOwner = gettext('None');
        }
        var networkId = '';
        try {
          networkId = port.network_id;
        }catch(e) {
          networkId = gettext('None');
        }
        object.ip_address = ipAddress;
        object.device_owner = deviceOwner;
        object.network_id = networkId;
        object.is_interface = (deviceOwner === 'router_interface');
        ports.push(object);
      });
    } else if (d.hasOwnProperty('subnets')) {
      angular.element.each(d.subnets, function(i, snet) {
        var object = {};
        object.id = snet.id;
        object.cidr = snet.cidr;
        object.url = snet.url;
        subnets.push(object);
      });
    }
    var htmlData = {
      balloon_id:balloonID,
      id:d.id,
      url:d.url,
      name:d.name,
      type:d.type,
      delete_label: gettext('Delete'),
      status:d.status,
      status_class: (d.status === 'ACTIVE') ? 'active' : 'down',
      status_label: gettext('STATUS'),
      id_label: gettext('ID'),
      interfaces_label: gettext('Interfaces'),
      subnets_label: gettext('Subnets'),
      delete_interface_label: gettext('Delete Interface'),
      delete_subnet_label: gettext('Delete Subnet'),
      open_console_label: gettext('Open Console'),
      view_details_label: gettext('View Details'),
      ips_label: gettext('IP Addresses')
    };
    var html;
    if (d instanceof Router) {
      htmlData.delete_label = gettext('Delete Router');
      htmlData.view_details_label = gettext('View Router Details');
      htmlData.port = ports;
      htmlData.add_interface_url = 'router/' + d.id + '/addinterface';
      htmlData.add_interface_label = gettext('Add Interface');
      html = balloonTmpl.render(htmlData,{
        table1:deviceTmpl,
        table2:portTmpl
      });
    } else if (d instanceof Server) {
      htmlData.delete_label = gettext('Terminate Instance');
      htmlData.view_details_label = gettext('View Instance Details');
      htmlData.console_id = d.id;
      htmlData.ips = d.ip_addresses;
      htmlData.console = d.console;
      html = balloonTmpl.render(htmlData,{
        table1:deviceTmpl,
        table2:instanceTmpl
      });
    } else if (d instanceof Network || d instanceof ExternalNetwork) {
      for (var s in subnets) {
        subnets[s].network_id = d.id;
      }
      htmlData.subnet = subnets;
      if (d instanceof Network) {
        htmlData.delete_label = gettext('Delete Network');
      }
      htmlData.add_subnet_url = 'network/' + d.id + '/subnet/create';
      htmlData.add_subnet_label = gettext('Create Subnet');
      html = balloonTmpl.render(htmlData,{
        table1:deviceTmpl,
        table2:netTmpl
      });
    } else {
      return;
    }
    angular.element(self.svg_container).append(html);
    var devicePosition = self.getScreenCoords(d2.x, d2.y);
    var x = devicePosition.x;
    var y = devicePosition.y;
    var xoffset = 100;
    var yoffset = 95;
    angular.element('#' + balloonID).css({
      'left': x + xoffset + 'px',
      'top': y + yoffset + 'px'
    }).show();
    var _balloon = angular.element('#' + balloonID);
    if (element.x + _balloon.outerWidth() > angular.element(window).outerWidth()) {
      _balloon
        .css({
          'left': 0 + 'px'
        })
        .css({
          'left': (x - _balloon.outerWidth() + 'px')
        })
        .addClass('leftPosition');
    }
    _balloon.find('.delete-device').click(function() {
      var _this = angular.element(this);
      _this.prop('disabled', true);
      d3.select('#id_' + _this.data('device-id')).classed('loading',true);
      self.delete_device(_this.data('type'),_this.data('device-id'));
    });
    _balloon.find('.delete-port').click(function() {
      var _this = angular.element(this);
      self.delete_port(_this.data('router-id'),_this.data('port-id'),_this.data('network-id'));
      self.delete_balloon();
    });
    self.balloonID = balloonID;
  },

  delete_balloon:function() {
    var self = this;
    if (self.balloonID) {
      angular.element('#' + self.balloonID).remove();
      self.balloonID = null;
      self.force.start();
    }
  },

  svgs: function(name) {
    switch (name) {
      case 'router':
        return 'm 26.628571,16.08 -8.548572,0 0,8.548571 2.08,-2.079998 6.308572,6.30857 4.38857,-4.388572 -6.308571,-6.30857 z m -21.2571429,-4.159999 8.5485709,0 0,-8.5485723 -2.08,2.08 L 5.5314281,-0.85714307 1.1428571,3.5314287 7.4514281,9.84 z m -3.108571,7.268571 0,8.548571 8.5485709,0 L 8.7314281,25.657144 15.039999,19.325715 10.674285,14.96 4.3428571,21.268573 z M 29.737142,8.8114288 l 0,-8.54857147 -8.548572,0 2.08,2.07999987 -6.308571,6.3085716 4.388572,4.3885722 6.308571,-6.3085723 z';
      default:
        return '';
    }
  },

  post_message: function(id,url,message) {
    var self = this;
    var iframeID = 'ifr_' + id;
    var iframe = angular.element('<iframe width="500" height="300" />')
      .attr('id',iframeID)
      .attr('src',url)
      .appendTo(self.post_messages);
    iframe.on('load',function() {
      angular.element(this).get(0).contentWindow.postMessage(
        JSON.stringify(message, null, 2), '*');
    });
  },
  delete_post_message: function(id) {
    angular.element('#' + id).remove();
  }
};
