/* Namespace for core functionality related to Network Topology. */
horizon.network_topology = {
  model: null,
  network_margin: 270,
  topologyCanvas_padding: 120,
  min_network_height:500,
  port_margin: 20,
  device_initial_position : 40,
  device_last_position : 0,
  device_left_position : 90,
  device_margin : 20,
  device_min_height : 45,
  port_initial_position: 1,
  network_index: {},
  network_color_unit: 0,
  network_saturation: 1,
  network_lightness: 0.7,
  reload_duration: 10000,
  spinner:null,
  init:function(){
    var self = this;
    $("#topologyCanvas").spin(horizon.conf.spinner_options.modal);
    self.retrieve_network_info();
    setInterval(function(){
      self.retrieve_network_info();
    }, self.reload_duration);
  },
  retrieve_network_info: function(){
    var self = this;
    if($("#networktopology").length === 0) {
        return;
    }
    $.getJSON($("#networktopology").data("networktopology"),
      function(data) {
        self.draw_graph(data);
      }
    );
  },
  draw_loading: function () {
    $("#topologyCanvas").spin(horizon.conf.spinner_options.modal);
  },
  draw_graph: function(data){
    var canvas = $("#topologyCanvas");
    var networks = $("#topologyCanvas > .networks");
    var nodata = $("#topologyCanvas > .nodata");
    networks.show();
    nodata.hide();
    canvas.spin(false);
    networks.empty();
    this.model = data;
    this.device_last_position = this.device_initial_position;
    var network_elements = this.draw_networks();
    var router_elements = this.draw_routers();
    var server_elements = this.draw_servers();
    if ((network_elements + router_elements + server_elements) <= 0){
      networks.hide();
      nodata.show();
    } else {
      canvas.height(
        Math.max(this.device_last_position + this.topologyCanvas_padding, this.min_network_height)
      );
      networks.width(
        this.model.networks.length * this.network_margin
      );
    }
  },
  network_color: function(network_id){
    var max_hue = 360;
    var num_network = this.model.networks.length;
    if(num_network <= 0){
      return;
    }
    num_network ++;
    var hue = Math.floor(
      max_hue/num_network*(this.network_index(network_id) + 1));
    return this.hsv2rgb(
      hue, this.network_saturation, this.network_lightness);
  },
  //see http://en.wikipedia.org/wiki/HSL_and_HSV
  hsv2rgb:function (h, s, v) {
      var hi = Math.round(h/60) % 6;
      var f = h/60 - hi;
      var p = v*(1 - s);
      var q = v*(1 - f*s);
      var t = v*(1 - (1 - f)*s);
      switch(hi){
        case 0:
          r = v;
          g = t;
          b = p;
          break;
        case 1:
          r = q;
          g = v;
          b = p;
          break;
        case 2:
          r = p;
          g = v;
          b = t;
          break;
        case 3:
          r = p;
          g = q;
          b = v;
          break;
        case 4:
          r = t;
          g = p;
          b = v;
          break;
        case 5:
          r = v;
          g = p;
          b = q;
          break;
      }
      return "rgb(" + Math.round(r*255) + "," + Math.round(g*255) + "," + Math.round(b*255) + ")";
  },
  draw_networks: function(){
    var self = this;
    var networks = $("#topologyCanvas > .networks");
    $.each(self.model.networks, function(index, network){
      var label = (network.name != "")? network.name : network.id;
      if(network['router:external']){
         label += " (external) ";
      }
      self.network_index[network.id] = index;
      var network_html = $("<div class='network' />").attr("id", network.id);
      var nicname_html = $("<div class='nicname'><h3>" + label +
        "</h3><span class='ip'>" + self.select_cidr(network.id) + "</span></div>");
      if (network.url == undefined) {
        nicname_html.addClass("nourl");
      } else {
        nicname_html.click(function (){
          window.location.href = network.url;
        });
      }
      nicname_html
        .css (
          {'background-color':self.network_color(network.id)})
        .appendTo(network_html);
      networks.append(network_html);
    });
    return self.model.networks.length;
  },
  select_cidr:function(network_id){
    var cidr = "";
    $.each(this.model.subnets, function(index, subnet){
        if(subnet.network_id != network_id){
            return;
        }
        cidr += subnet.cidr;
    });
    return cidr;
  },
  draw_devices: function(type){
    var self = this;
    $.each(self.model[type + 's'], function(index, device){
      var id = device.id;
      var name = (device.name != "")? device.name : device.id;
      var ports = self.select_port(id);
      if(ports.length <= 0){
          return;
      }
      var main_port = self.select_main_port(ports);
      var parent_network = main_port.network_id;
      var device_html = $("<div class='" + type + "'></div>");
      device_html
        .attr('id', device.id)
        .css({top: self.device_last_position, position: 'absolute'})
        .append($("<span class='devicename'><i></i>" + type + "</span>"))
        .click(function (e){
          e.stopPropagation();
          window.location.href = device.url;
        });
      var name_html = $("<span class='name'></span>")
        .html(device.name)
        .attr('title', device.name)
        .appendTo(device_html);
      var port_position = self.port_initial_position;
      $.each(ports, function(){
          var port = this;
          var port_html = self.port_html(port);
          port_position += self.port_margin;
          self.port_css(port_html, port_position, parent_network, port.network_id);
          device_html.append(port_html);
      });
      port_position += self.port_margin;
      device_html.css(
        {height: Math.max(self.device_min_height, port_position) + "px"});
      self.device_last_position += device_html.height() + self.device_margin;
      $("#" + parent_network).append(device_html);
    });
    return self.model[type + 's'].length;
  },
  sum_port_length: function(network_id, ports){
    var self = this;
    var sum_port_length = 0;
    var base_index = self.network_index(network_id);
    $.each(ports, function(index, port){
      sum_port_length += base_index - self.network_index(port.network_id);
    });
    return sum_port_length;
  },
  select_main_port: function(ports){
    var main_port_index = 0;
    var MAX_INT = 4294967295;
    var min_port_length = MAX_INT;
    $.each(ports, function(index, port){
      port_length = horizon.network_topology.sum_port_length(port.network_id, ports)
      if(port_length < min_port_length){
        min_port_length = port_length;
        main_port_index = index;
      }
    })
    return ports[main_port_index];
  },
  draw_routers: function(){
      return this.draw_devices('router');
  },
  draw_servers: function(){
      return this.draw_devices('server');
  },
  select_port: function(device_id){
     return $.map(this.model.ports,function(port, index){
        if (port.device_id == device_id) {
          return port;
        }
     });
  },
  port_html: function(port){
    var self = this;
    var port_html = $('<div class="port"><div class="dot"></div></div>');
    var ip_label = "";
    $.each(port.fixed_ips, function(){
      ip_label += this.ip_address + " ";
    })
    var ip_html = $('<span class="ip" />').html(ip_label);
    port_html
      .append(ip_html)
      .css({'background-color':self.network_color(port.network_id)})
      .click(function (e) {
        e.stopPropagation();
        if(port.url != undefined) {
          window.location.href = port.url;
        }
      });
    if(port.url == undefined) {
      port_html.addClass("nourl");
    }
    return port_html;
  },
  port_css: function(port_html, position, network_a, network_b){
    var self = this;
    var index_diff = self.network_index(network_a) - self.network_index(network_b);
    var width = self.network_margin * index_diff;
    var direction = "left";
    if(width < 0){
        direction = "right";
        width += self.network_margin;
    }
    width = Math.abs(width) + self.device_left_position;
    var port_css = {};
    port_css['width'] = width + "px";
    port_css['top'] = position + "px";
    port_css[direction] = (-width -3) + "px";
    port_html.addClass(direction).css(port_css);
  },
  network_index: function(network_id){
    return horizon.network_topology.network_index[network_id];
  }
}

horizon.addInitFunction(function () {
    horizon.network_topology.init();
});
