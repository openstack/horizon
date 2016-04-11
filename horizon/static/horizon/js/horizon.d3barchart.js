/*
  Used for animating and displaying bar information using
  D3js rect.

  Usage:
    In order to have single bars that work with this, you need to have a
    DOM structure like this in your Django template:

    Example:
    <div style="width: 100px; min-width: 100px; height: 20px; min-height: 20px">
      <div class="chart"
        data-chart-type="bar_chart"
        data-tooltip-used='Used'
        data-tooltip-free='Free'
        data-tooltip-average='Average'
        data-settings='{"orientation": "horizontal"}'
        data-used="20"
        data-average="30">
      </div>
    </div>

    The available data- attributes are:
      data-tooltip-free, data-tooltip-used, data-tooltip-average OPTIONAL
        Html content of tooltips that will be displayed over this areas.


      data-used="integer" REQUIRED
        1. Integer
          Integer representing the percent used.
        2. Array
          Array of following structure:
            [
              {"tooltip_used": "Popup html 1", "used_instances": "5"},
              {"tooltip_used": "Popup html 2", "used_instances": "15"},....
            ]

          used_instances: Integer representing the percent used.
          tooltip_used: Html that will be displayed in tooltip window over
            this area.

      data-settings="JSON"
        Json with variety of settings described below.

          used-label-placement='string' OPTIONAL
            String determining where the floating label stating number of percent
            will be placed. So far only left is supported.

          width="integer" OPTIONAL
            Integer in pixels. Determines the total width of the bar. Handy when
            we use a used_label, so the bar is not a 100% of the container.

          average="integer" OPTIONAL
            Integer representing the average usage in percent of given
            single-bar.

          auto-scale-selector OPTIONAL
            Jquery selector of bar elements that have Integer
            used attribute.

          orientation OPTIONAL
            String representing orientation of the bar.Can be "horizontal"
            or "vertical". Default is horizontal.

*/

horizon.d3_bar_chart = {
  /**
   * A class representing the bar chart
   * @param chart_module A context of horizon.d3_line_chart module.
   * @param html_element A html_element containing the chart.
   * @param settings An object containing settings of the chart.
   */
  BarChart: function(chart_module, html_element, settings, data){
    var self = this;
    self.chart_module = chart_module;
    self.html_element = html_element;
    self.jquery_element = $(self.html_element);

    /************************************************************************/
    /*********************** Initialization methods *************************/
    /************************************************************************/
    /**
     * Initialize the object.
     */
    self.init = function(settings, data) {
      var self = this;
      self.data = {};

      self.data.max_value = self.jquery_element.data('max-value');
      if (!self.max_value){
        // Default mas value is 100, representing 100 percent
        self.max_value = 100;
      }

      // Chart data
      self.data.used = self.jquery_element.data('used');
      self.data.average = self.jquery_element.data('average');

      // Tooltips data
      self.data.tooltip_average = self.jquery_element.data('tooltip-average');
      self.data.tooltip_free = self.jquery_element.data('tooltip-free');
      self.data.tooltip_used = self.jquery_element.data('tooltip-used');

      if (data !== undefined){
        if (data.used !== undefined){
          self.data.used = data.used;
        }
        if (data.average !== undefined){
          self.data.average = data.average;
        }
        if (data.tooltip_average !== undefined){
          self.data.tooltip_average = data.tooltip_average;
        }
        if (data.tooltip_free !== undefined){
          self.data.tooltip_free = data.tooltip_free;
        }
        if (data.tooltip_used !== undefined){
          self.data.tooltip_used = data.tooltip_used;
        }
      }

      // Percentage count
      if ($.isArray(self.data.used)){
        self.data.percentage_average = 0; // No average for Multi-bar chart
        self.data.percentage_used = Array();
        self.data.tooltip_used_contents = Array();
        for (var i = 0; i < self.data.used.length; ++i) {
          if (!isNaN(self.max_value) && !isNaN(self.data.used[i].used_instances)) {
            var used = Math.round((self.data.used[i].used_instances / self.max_value) * 100);

            self.data.percentage_used.push(used);
            // for multi-bar chart, tooltip is in the data
            self.data.tooltip_used_contents.push(self.data.used[i].tooltip_used);
          } else { // If NaN self.data.percentage_used is 0

          }
        }
      } else {
        if (!isNaN(self.max_value) && !isNaN(self.data.used)) {
          self.data.percentage_used = Math.round((self.data.used / self.max_value) * 100);
        } else { // If NaN self.data.percentage_used is 0
          self.data.percentage_used = 0;
        }

        if (!isNaN(self.max_value) && !isNaN(self.data.average)) {
          self.data.percentage_average = ((self.data.average / self.max_value) * 100);
        } else {
          self.data.percentage_average = 0;
        }
      }

      // Load initial settings.
      self.init_settings(settings);
    };

    /**
     * Initialize settings of the chart with default values, then applies
     * defined settings of the chart. Settings are obtained either from JSON
     * of the html attribute data-settings, or from init of the charts. The
     * highest priority settings are obtained directly from the JSON data
     * obtained from the server.
     * @param settings An object containing settings of the chart.
     */
    self.init_settings = function(settings) {
      var self = this;

      self.data.settings = {};

      // Orientation of the Bar chart
      self.data.settings.orientation = 'horizontal';

      // Width and height of bar
      self.data.settings.width = self.jquery_element.data('width');
      self.data.settings.height = self.jquery_element.data('height');

      /* Applying settings. The later application rewrites the previous
         therefore it has bigger priority. */

      // Settings defined in the init method of the chart
      if (settings){
        self.apply_settings(settings);
      }

      // Settings defined in the html data-settings attribute
      if (self.jquery_element.data('settings')){
        var inline_settings = self.jquery_element.data('settings');
        self.apply_settings(inline_settings);
      }
    };

    /**
     * Applies passed settings to the chart object. Allowed settings are
     * listed in this method.
     * @param settings An object containing settings of the chart.
     */
    self.apply_settings = function(settings){
      var self = this;
      var allowed_settings = ['orientation', 'used_label_placement',
                              'width', 'height'];

      $.each(allowed_settings, function(index, setting_name) {
        if (settings[setting_name] !== undefined){
          self.data.settings[setting_name] = settings[setting_name];
        }
      });
    };

    /************************************************************************/
    /****************************** Initialization **************************/
    /************************************************************************/
    // Init the object
    self.init(settings, data);

    /************************************************************************/
    /****************************** Methods *********************************/
    /************************************************************************/
    /**
     * Obtains the actual chart data and renders the chart again.
     */
    self.refresh = function(){
      var self = this;
      // Clear the chart before rendering it
      self.jquery_element.empty();
      self.render();
    };

    /**
     * Renders the chart into html element given in initializer.
     */
    self.render = function() {
      var self = this;

      // Initialize wrapper
      var wrapper = new self.chart_module.Wrapper(self.chart_module, self.html_element, self.data);

      // Append Unused resources Bar
      (new self.chart_module.UnusedComponent(wrapper)).render(self.data.tooltip_free);

      if (wrapper.used_multi()){
        // If UsedComponent is shown as multiple values in one chart
        for (var i = 0; i < wrapper.percentage_used.length; ++i) {
          // FIXME write proper iterator
          wrapper.used_multi_iterator = i;

          // Append used so it will be shown as multiple values in one chart
          (new self.chart_module.UsedComponent(wrapper)).render(self.data.tooltip_used);

          // Compute total value as a start point for next Used bar
          wrapper.total_used_perc += wrapper.percentage_used_value();
          wrapper.total_used_value_in_pixels = (wrapper.w / 100) * wrapper.total_used_perc;
        }

      } else {
        // Used is show as one value it the chart
        (new self.chart_module.UsedComponent(wrapper)).render(self.data.tooltip_used);
        // Append average value to Bar
        (new self.chart_module.AverageComponent(wrapper)).render(self.data.tooltip_average);
      }
    };
  },
  /**
   * Chart wrapper class renders the main svg element and encapsulate
   * the chart data.
   * @param chart_module Chart module name
   * @param html_element HTML element where the chart will be rendered
   * @param chart_module Data + settings of the chart
   */
  Wrapper: function(chart_module, html_element, data){
    var self = this;
    self.html_element = html_element;
    self.jquery_element = $(html_element);

    // Bar HTML element
    self.bar_html = d3.select(html_element);
    // Bar layout for bar chart
    self.bar = self.bar_html.append('svg:svg')
      .attr('class', 'legacy-bar-chart');

    // Get correct size of chart and the wrapper.
    chart_module.get_size(self.html_element);

    self.data = data;
    // Floating label of used bar placement
    self.used_label_placement = data.settings.used_label_placement;

    // Width and height of the chart itself
    if (data.settings.width !== undefined){
      self.w = parseFloat(data.settings.width);
    } else {
      self.w = parseFloat(self.jquery_element.width());
    }
    if (data.settings.height !== undefined) {
      self.h = parseFloat(data.settings.height);
    } else {
      self.h = parseFloat(self.jquery_element.height());
    }

    /* Start coordinations of the chart and size of the chart wrapper.
       Chart can have other elements next to it, so it doesn't have to
       start at 0.
    */
    self.chart_start_x = 0;
    if (self.data.settings.orientation === 'vertical'){
      if (self.used_label_placement === 'left'){
        self.chart_start_x = 44;
      }
      self.chart_wrapper_w = self.w + self.chart_start_x;
    } else {
      self.chart_wrapper_w = self.w;
    }
    self.chart_wrapper_h = self.h;

    // Basic settings of the chart
    self.lvl_curve = 3;

    // Percentage used
    self.percentage_used = data.percentage_used;
    self.total_used_perc = 0; // incremented in render method
    self.total_used_value_in_pixels = 0; // incremented in render method
    self.used_value_in_pixels = 0; // set in UsedComponent
    self.average_value_in_pixels = 0; // set in AverageComponent


    // Percentage average
    self.percentage_average = data.percentage_average;
    self.tooltip_used_contents = data.tooltip_used_contents;

    // Border of the chart
    self.border_width = 1;

    // Return true if it renders multiple used percentage in one chart
    self.used_multi = function (){
      return ($.isArray(self.percentage_used));
    };

    // Deals with percentage if there should be multiple in one chart
    self.used_multi_iterator = 0;
    self.percentage_used_value = function(){
      if (self.used_multi()){
        return self.percentage_used[self.used_multi_iterator];
      } else {
        return self.percentage_used;
      }
    };

    // Deals with html tooltips if there should be multiple in one chart
    self.tooltip_used_value = function (){
      if (self.used_multi()){
        return self.tooltip_used_contents[self.used_multi_iterator];
      } else {
        return '';
      }
    };

    // Return true if it chart is oriented horizontally
    self.horizontal_orientation = function (){
      return (self.data.settings.orientation === 'horizontal');
    };
  },
  /**
   * Component rendering part of chart showing 'used', optional labels
   * and optional tool-tip element.
   * the chart data.
   * @param wrapper Wrapper object
   */
  UsedComponent: function(wrapper){
    var self = this;
    self.wrapper = wrapper;

    // FIXME(lsmola) would be good to abstract all attributes and resolve orientation inside
    if (self.wrapper.horizontal_orientation()){
      // Horizontal Bars
      self.wrapper.used_value_in_pixels = (self.wrapper.w / 100) * self.wrapper.percentage_used_value();

      self.y = 0;
      self.x = self.wrapper.total_used_value_in_pixels;
      self.width = 0;
      self.height = self.wrapper.h;
      self.trasition_attr = 'width';
      self.trasition_value = self.wrapper.used_value_in_pixels;
    } else {
      // Vertical Bars
      self.wrapper.used_value_in_pixels = (self.wrapper.h / 100) * self.wrapper.percentage_used_value();

      self.y = self.wrapper.h;
      self.x = self.wrapper.chart_start_x;
      self.width = self.wrapper.w - self.wrapper.border_width;
      self.height = self.wrapper.used_value_in_pixels;
      self.trasition_attr = 'y';
      self.trasition_value = self.wrapper.h - self.wrapper.used_value_in_pixels;
    }

    self.render = function(tooltip){
      var elem = self.wrapper.bar.append('rect')
        .attr('class', 'used_component legacy-bar-chart-section')
        .attr('y', self.y)
        .attr('x', self.x)
        .attr('width', self.width)
        .attr('height', self.height)
        .attr('d', self.wrapper.percentage_used_value())
        .transition()
          .duration(500)
          .attr(self.trasition_attr, self.trasition_value);

      $(elem).tooltip({
        placement: self.wrapper.data.settings.orientation === 'horizontal' ? 'bottom' : 'left',
        container: 'body',
        title: $.isArray(self.wrapper.data.percentage_used) ? self.wrapper.tooltip_used_value() : tooltip
      });

      if (self.wrapper.used_label_placement === 'left') {
        // Now it works only for vertical bar chart placed left form the chart
        var label_placement_y = self.wrapper.h - self.wrapper.used_value_in_pixels;

        // Make sure the placement will be visible with border values
        if (label_placement_y <= 6){
          label_placement_y = 6;
        } else if (label_placement_y >= (self.wrapper.h - 6)){
          label_placement_y = self.wrapper.h - 6;
        }

        // Append label text
        self.wrapper.bar.append('text')
          .attr('class', 'used_component_label')
          .text(self.wrapper.percentage_used_value() + '%')
          .attr('y', label_placement_y)
          .attr('x', 0)
          .attr('dominant-baseline', 'middle')
          .transition()
            .duration(500)
            .attr('x', function() {
              if (self.wrapper.percentage_used_value() > 99){
                // If there are two digits, label have to be farther to the bar chart
                return 0;
              }
              else if (self.wrapper.percentage_used_value() > 9){
                // If there are two digits, label have to be farther to the bar chart
                return 4;
              }
              else {
                // If there is only one digit, label can be closer to the bar chart
                return 8;
              }
            });

        // Append little triangle pointing to text
        var poly = [{'x':self.wrapper.chart_start_x - 8, 'y':label_placement_y},
                {'x':self.wrapper.chart_start_x - 3,'y':label_placement_y + 2},
                {'x':self.wrapper.chart_start_x - 3,'y':label_placement_y - 2}
               ];

        self.wrapper.bar.selectAll('polygon')
          .data([poly])
          .enter()
          .append('polygon')
          .attr('class', 'used_component_label_arrow')
          .attr('points',function(d) {
            return d.map(function(d) {
              return [d.x,d.y].join(',');
            }).join(' ');
          })
          .attr('stroke-width', 2);
      }
    };
  },
  /**
   * Component rendering part of chart showing 'average' and optional
   * tool-tip element.
   * the chart data.
   * @param wrapper Wrapper object
   */
  AverageComponent: function(wrapper){
    var self = this;
    self.wrapper = wrapper;

    // FIXME would be good to abstract all attributes and resolve orientation inside
    if (wrapper.horizontal_orientation()){
      // Horizontal Bars
      self.wrapper.average_value_in_pixels = (self.wrapper.w / 100) * self.wrapper.percentage_average;

      self.y = 1;
      self.x = self.wrapper.average_value_in_pixels;
      self.width = 0;
      self.height = self.wrapper.h;
    } else { // Vertical Bars
      self.wrapper.average_value_in_pixels = (self.wrapper.h / 100) * (100 - self.wrapper.percentage_average);

      self.y = self.wrapper.average_value_in_pixels;
      self.x = self.wrapper.chart_start_x;
      self.width = self.wrapper.w - self.wrapper.border_width;
      self.height = 0;
    }

    self.render = function(tooltip){
      if (self.wrapper.percentage_average > 0) {
        // Only show average when it is bigger than 0
        // A dashed line

        var elem = self.wrapper.bar.append('line')
          .attr('class', 'average_component')
          .attr('y1', self.y)
          .attr('x1', self.x)
          .attr('y2', self.y + self.height)
          .attr('x2', self.x + self.width);

        $(elem).tooltip({
          placement: self.wrapper.data.settings.orientation === 'horizontal' ? 'top' : 'right',
          container: 'body',
          title: tooltip
        });
      }
    };
  },
  /**
   * Component rendering part of chart showing 'unused' and optional
   * tool-tip element.
   * the chart data.
   * @param wrapper Wrapper object
   */
  UnusedComponent: function(wrapper){
    var self = this;
    self.wrapper = wrapper;

    self.render = function(tooltip){
      var elem = self.wrapper.bar.append('rect')
        .attr('class', 'unused_component legacy-bar-chart-section')
        .attr('y', 0)
        .attr('x', self.wrapper.chart_start_x)
        .attr('width', self.wrapper.w)
        .attr('height', self.wrapper.h)
        .attr('rx', self.wrapper.lvl_curve)
        .attr('ry', self.wrapper.lvl_curve);

      $(elem).tooltip({
        placement: self.wrapper.data.settings.orientation === 'horizontal' ? 'bottom' : 'left',
        container: 'body',
        title: tooltip
      });
    };
  },
  /**
   * Function for initializing of the charts.
   * @param selector JQuery selector of charts we want to initialize.
   * @param settings An object containing settings of the chart.
   * @param data An object containing data of the chart.
   */
  init: function(selector, settings, data) {
    var self = this;
    self.bars = $(selector);

    self.bars.each(function() {
      self.refresh(this, settings, data);
    });
  },
  /**
   * Function for creating chart objects, saving them for later reuse
   * and calling their refresh method.
   * @param html_element HTML element where the chart will be rendered.
   * @param settings An object containing settings of the chart.
   * @param data An object containing data of the chart.
   */
  refresh: function(html_element, settings, data){
    var chart = new this.BarChart(this, html_element, settings, data);
    // FIXME save chart objects somewhere so I can use them again when
    // e.g. I am switching tabs, or if I want to update them
    // via web sockets
    // this.charts.add_or_update(chart)
    chart.refresh();
  },
  /**
   * Function for computing size of the chart from the surrounding HTML.
   * @param html_element HTML element where the chart will be rendered.
   */
  get_size: function(html_element){
    /* The height will be determined by css or window size,
       I have to hide everything inside that could mess with
       the size, so it is fully determined by outer CSS. */
    var jquery_element = $(html_element);
    jquery_element.css('height', '');
    jquery_element.css('width', '');
    var svg = jquery_element.find('svg');
    svg.hide();

    // Width and height of the chart will be taken from chart wrapper,
    // that can be styled by css.
    var width = jquery_element.width();

    // Set either the minimal height defined by CSS.
    var height = jquery_element.height();

    /* Setting new sizes. It is important when resizing a window.*/
    jquery_element.css('height', height);
    jquery_element.css('width', width);
    svg.show();
    svg.css('height', height);
    svg.css('width', width);
  }
};


horizon.addInitFunction(function () {
  horizon.d3_bar_chart.init('div[data-chart-type="bar_chart"]', {}, {});
});
