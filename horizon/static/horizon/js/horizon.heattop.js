/**
 *
 * HeatTop JS Framework
 * Dependencies: jQuery 1.7.1 or later, d3 v3 or later
 * Date: June 2013
 * Description: JS Framework that subclasses the D3 Force Directed Graph library to create
 * Heat-specific objects and relationships with the purpose of displaying
 * Stacks, Resources, and related Properties in a Resource Topology Graph.
 *
 * Licensed under the Apache License, Version 2.0 (the "License"); you may
 * not use this file except in compliance with the License. You may obtain
 * a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
 * WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
 * License for the specific language governing permissions and limitations
 * under the License.
 */

var container = "#heat_resource_topology";

function update(){
  node = node.data(nodes, function(d) { return d.name; });
  link = link.data(links);

  var nodeEnter = node.enter().append("g")
    .attr("class", "node")
    .attr("node_name", function(d) { return d.name; })
    .attr("node_id", function(d) { return d.instance; })
    .call(force.drag);

  nodeEnter.append("image")
    .attr("xlink:href", function(d) { return d.image; })
    .attr("id", function(d){ return "image_"+ d.name; })
    .attr("x", function(d) { return d.image_x; })
    .attr("y", function(d) { return d.image_y; })
    .attr("width", function(d) { return d.image_size; })
    .attr("height", function(d) { return d.image_size; });
  node.exit().remove();

  link.enter().insert("svg:line", "g.node")
    .attr("class", "link")
    .style("stroke-width", function(d) { return Math.sqrt(d.value); });
  link.exit().remove();
  //Setup click action for all nodes
  node.on("mouseover", function(d) {
    $("#info_box").html(d.info_box);
    current_info = d.name;
  });
  node.on("mouseout", function(d) {
    $("#info_box").html('');
  });

  force.start();
}

function tick() {
  link.attr("x1", function(d) { return d.source.x; })
    .attr("y1", function(d) { return d.source.y; })
    .attr("x2", function(d) { return d.target.x; })
    .attr("y2", function(d) { return d.target.y; });

  node.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
}

function set_in_progress(stack, nodes) {
  if (stack.in_progress === true) { in_progress = true; }
  for (var i = 0; i < nodes.length; i++) {
    var d = nodes[i];
    if (d.in_progress === true){ in_progress = true; return false; }
  }
}

function findNode(name) {
  for (var i = 0; i < nodes.length; i++) {
    if (nodes[i].name === name){ return nodes[i]; }
  }
}

function findNodeIndex(name) {
  for (var i = 0; i < nodes.length; i++) {
    if (nodes[i].name === name){ return i; }
  }
}

function addNode (node) {
  nodes.push(node);
  needs_update = true;
}

function removeNode (name) {
  var i = 0;
  var n = findNode(name);
  while (i < links.length) {
    if (links[i].source === n || links[i].target === n) {
      links.splice(i, 1);
    } else {
      i++;
    }
  }
  nodes.splice(findNodeIndex(name),1);
  needs_update = true;
}

function remove_nodes(old_nodes, new_nodes){
  //Check for removed nodes
  for (var i=0;i<old_nodes.length;i++) {
    var remove_node = true;
    for (var j=0;j<new_nodes.length;j++) {
      if (old_nodes[i].name === new_nodes[j].name){
        remove_node = false;
        break;
      }
    }
    if (remove_node === true){
      removeNode(old_nodes[i].name);
    }
  }
}

function build_links(){
  for (var i=0;i<nodes.length;i++){
    build_node_links(nodes[i]);
    build_reverse_links(nodes[i]);
  }
}

function build_node_links(node){
  for (var j=0;j<node.required_by.length;j++){
    var push_link = true;
    var target_idx = '';
    var source_idx = findNodeIndex(node.name);
    //make sure target node exists
    try {
      target_idx = findNodeIndex(node.required_by[j]);
    } catch(err) {
      push_link =false;
    }
    //check for duplicates
    for (var lidx=0;lidx<links.length;lidx++) {
      if (links[lidx].source === source_idx && links[lidx].target === target_idx) {
        push_link=false;
        break;
      }
    }

    if (push_link === true && (source_idx && target_idx)){
      links.push({
        'source':source_idx,
        'target':target_idx,
        'value':1
      });
    }
  }
}

function build_reverse_links(node){
  for (var i=0;i<nodes.length;i++){
    if(nodes[i].required_by){
      for (var j=0;j<nodes[i].required_by.length;j++){
        var dependency = nodes[i].required_by[j];
        //if new node is required by existing node, push new link
        if(node.name === dependency){
          links.push({
            'source':findNodeIndex(nodes[i].name),
            'target':findNodeIndex(node.name),
            'value':1
          });
        }
      }
    }
  }
}

function ajax_poll(poll_time){
  setTimeout(function() {
    $.getJSON(ajax_url, function(json) {
      //update d3 data element
      $("#d3_data").attr("data-d3_data", JSON.stringify(json));

      //update stack
      $("#stack_box").html(json.stack.info_box);
      set_in_progress(json.stack, json.nodes);
      needs_update = false;

      //Check Remove nodes
      remove_nodes(nodes, json.nodes);

      //Check for updates and new nodes
      json.nodes.forEach(function(d){
        current_node = findNode(d.name);
        //Check if node already exists
        if (current_node) {
          //Node already exists, just update it
          current_node.status = d.status;

          //Status has changed, image should be updated
          if (current_node.image !== d.image){
            current_node.image = d.image;
            var this_image = d3.select("#image_"+current_node.name);
            this_image
              .transition()
              .attr("x", function(d) { return d.image_x + 5; })
              .duration(100)
              .transition()
              .attr("x", function(d) { return d.image_x - 5; })
              .duration(100)
              .transition()
              .attr("x", function(d) { return d.image_x + 5; })
              .duration(100)
              .transition()
              .attr("x", function(d) { return d.image_x - 5; })
              .duration(100)
              .transition()
              .attr("xlink:href", d.image)
              .transition()
              .attr("x", function(d) { return d.image_x; })
              .duration(100)
              .ease("bounce");
          }

          //Status has changed, update info_box
          current_node.info_box = d.info_box;

        } else {
          addNode(d);
          build_links();
        }
      });

      //if any updates needed, do update now
      if (needs_update === true){
        update();
      }
    });
    //if no nodes still in progress, slow AJAX polling
    if (in_progress === false) { poll_time = 30000; }
    else { poll_time = 3000; }
    ajax_poll(poll_time);
  }, poll_time);
}

if ($(container).length){
  var width = $(container).width(),
    height = 500,
    stack_id = $("#stack_id").data("stack_id"),
    ajax_url = '/project/stacks/get_d3_data/' + stack_id + '/',
    graph = $("#d3_data").data("d3_data"),
    force = d3.layout.force()
      .nodes(graph.nodes)
      .links([])
      .gravity(0.1)
      .charge(-2000)
      .linkDistance(100)
      .size([width, height])
      .on("tick", tick),
    svg = d3.select(container).append("svg")
      .attr("width", width)
      .attr("height", height),
    node = svg.selectAll(".node"),
    link = svg.selectAll(".link"),
    needs_update = false,
    nodes = force.nodes(),
    links = force.links();

  build_links();
  update();

  //Load initial Stack box
  $("#stack_box").html(graph.stack.info_box);
  //On Page load, set Action In Progress
  var in_progress = false;
  set_in_progress(graph.stack, node);

  //If status is In Progress, start AJAX polling
  var poll_time = 0;
  if (in_progress === true) { poll_time = 3000; }
  else { poll_time = 30000; }
  ajax_poll(poll_time);
}
