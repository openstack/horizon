/*
Copyright (c) Django Software Foundation and individual contributors.
All rights reserved.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

    1. Redistributions of source code must retain the above copyright notice, 
       this list of conditions and the following disclaimer.
    
    2. Redistributions in binary form must reproduce the above copyright 
       notice, this list of conditions and the following disclaimer in the
       documentation and/or other materials provided with the distribution.

    3. Neither the name of Django nor the names of its contributors may be used
       to endorse or promote products derived from this software without
       specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

// Handles related-objects functionality: lookup link for raw_id_fields
// and Add Another links.

function html_unescape(text) {
    // Unescape a string that was escaped using django.utils.html.escape.
    text = text.replace(/&lt;/g, '<');
    text = text.replace(/&gt;/g, '>');
    text = text.replace(/&quot;/g, '"');
    text = text.replace(/&#39;/g, "'");
    text = text.replace(/&amp;/g, '&');
    return text;
}

// IE doesn't accept periods or dashes in the window name, but the element IDs
// we use to generate popup window names may contain them, therefore we map them
// to allowed characters in a reversible way so that we can locate the correct 
// element when the popup window is dismissed.
function id_to_windowname(text) {
    text = text.replace(/\./g, '__dot__');
    text = text.replace(/\-/g, '__dash__');
    return text;
}

function windowname_to_id(text) {
    text = text.replace(/__dot__/g, '.');
    text = text.replace(/__dash__/g, '-');
    return text;
}

function showRelatedObjectLookupPopup(triggeringLink) {
    var name = triggeringLink.id.replace(/^lookup_/, '');
    name = id_to_windowname(name);
    var href;
    if (triggeringLink.href.search(/\?/) >= 0) {
        href = triggeringLink.href + '&pop=1';
    } else {
        href = triggeringLink.href + '?pop=1';
    }
    var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
    win.focus();
    return false;
}

function dismissRelatedLookupPopup(win, chosenId) {
    var name = windowname_to_id(win.name);
    var elem = document.getElementById(name);
    if (elem.className.indexOf('vManyToManyRawIdAdminField') != -1 && elem.value) {
        elem.value += ',' + chosenId;
    } else {
        document.getElementById(name).value = chosenId;
    }
    win.close();
}

function showAddAnotherPopup(triggeringLink) {
    var name = triggeringLink.id.replace(/^add_/, '');
    name = id_to_windowname(name);
    href = triggeringLink.href
    if (href.indexOf('?') == -1) {
        href += '?_popup=1';
    } else {
        href  += '&_popup=1';
    }
    var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
    win.focus();
    return false;
}

function dismissAddAnotherPopup(win, newId, newRepr) {
    // newId and newRepr are expected to have previously been escaped by
    // django.utils.html.escape.
    newId = html_unescape(newId);
    newRepr = html_unescape(newRepr);
    var name = windowname_to_id(win.name);
    var elem = document.getElementById(name);
    if (elem) {
        if (elem.nodeName == 'SELECT') {
            var o = new Option(newRepr, newId);
            elem.options[elem.options.length] = o;
            o.selected = true;
        } else if (elem.nodeName == 'INPUT') {
            if (elem.className.indexOf('vManyToManyRawIdAdminField') != -1 && elem.value) {
                elem.value += ',' + newId;
            } else {
                elem.value = newId;
            }
        }
    } else {
        var toId = name + "_to";
        elem = document.getElementById(toId);
        var o = new Option(newRepr, newId);
        SelectBox.add_to_cache(toId, o);
        SelectBox.redisplay(toId);
    }
    win.close();
}

/* gettext library */

var catalog = new Array();

function pluralidx(count) { return (count == 1) ? 0 : 1; }


function gettext(msgid) {
  var value = catalog[msgid];
  if (typeof(value) == 'undefined') {
    return msgid;
  } else {
    return (typeof(value) == 'string') ? value : value[0];
  }
}

function ngettext(singular, plural, count) {
  value = catalog[singular];
  if (typeof(value) == 'undefined') {
    return (count == 1) ? singular : plural;
  } else {
    return value[pluralidx(count)];
  }
}

function gettext_noop(msgid) { return msgid; }

function interpolate(fmt, obj, named) {
  if (named) {
    return fmt.replace(/%\(\w+\)s/g, function(match){return String(obj[match.slice(2,-2)])});
  } else {
    return fmt.replace(/%s/g, function(match){return String(obj.shift())});
  }
}

//Core javascript helper functions

//basic browser identification & version
var isOpera = (navigator.userAgent.indexOf("Opera")>=0) && parseFloat(navigator.appVersion);
var isIE = ((document.all) && (!isOpera)) && parseFloat(navigator.appVersion.split("MSIE ")[1].split(";")[0]);

//Cross-browser event handlers.
function addEvent(obj, evType, fn) {
 if (obj.addEventListener) {
     obj.addEventListener(evType, fn, false);
     return true;
 } else if (obj.attachEvent) {
     var r = obj.attachEvent("on" + evType, fn);
     return r;
 } else {
     return false;
 }
}

function removeEvent(obj, evType, fn) {
 if (obj.removeEventListener) {
     obj.removeEventListener(evType, fn, false);
     return true;
 } else if (obj.detachEvent) {
     obj.detachEvent("on" + evType, fn);
     return true;
 } else {
     return false;
 }
}

//quickElement(tagType, parentReference, textInChildNode, [, attribute, attributeValue ...]);
function quickElement() {
 var obj = document.createElement(arguments[0]);
 if (arguments[2] != '' && arguments[2] != null) {
     var textNode = document.createTextNode(arguments[2]);
     obj.appendChild(textNode);
 }
 var len = arguments.length;
 for (var i = 3; i < len; i += 2) {
     obj.setAttribute(arguments[i], arguments[i+1]);
 }
 arguments[1].appendChild(obj);
 return obj;
}

//----------------------------------------------------------------------------
//Cross-browser xmlhttp object
//from http://jibbering.com/2002/4/httprequest.html
//----------------------------------------------------------------------------
var xmlhttp;
/*@cc_on @*/
/*@if (@_jscript_version >= 5)
 try {
     xmlhttp = new ActiveXObject("Msxml2.XMLHTTP");
 } catch (e) {
     try {
         xmlhttp = new ActiveXObject("Microsoft.XMLHTTP");
     } catch (E) {
         xmlhttp = false;
     }
 }
@else
 xmlhttp = false;
@end @*/
if (!xmlhttp && typeof XMLHttpRequest != 'undefined') {
xmlhttp = new XMLHttpRequest();
}

//----------------------------------------------------------------------------
//Find-position functions by PPK
//See http://www.quirksmode.org/js/findpos.html
//----------------------------------------------------------------------------
function findPosX(obj) {
 var curleft = 0;
 if (obj.offsetParent) {
     while (obj.offsetParent) {
         curleft += obj.offsetLeft - ((isOpera) ? 0 : obj.scrollLeft);
         obj = obj.offsetParent;
     }
     // IE offsetParent does not include the top-level 
     if (isIE && obj.parentElement){
         curleft += obj.offsetLeft - obj.scrollLeft;
     }
 } else if (obj.x) {
     curleft += obj.x;
 }
 return curleft;
}

function findPosY(obj) {
 var curtop = 0;
 if (obj.offsetParent) {
     while (obj.offsetParent) {
         curtop += obj.offsetTop - ((isOpera) ? 0 : obj.scrollTop);
         obj = obj.offsetParent;
     }
     // IE offsetParent does not include the top-level 
     if (isIE && obj.parentElement){
         curtop += obj.offsetTop - obj.scrollTop;
     }
 } else if (obj.y) {
     curtop += obj.y;
 }
 return curtop;
}

//-----------------------------------------------------------------------------
//Date object extensions
//----------------------------------------------------------------------------
Date.prototype.getCorrectYear = function() {
 // Date.getYear() is unreliable --
 // see http://www.quirksmode.org/js/introdate.html#year
 var y = this.getYear() % 100;
 return (y < 38) ? y + 2000 : y + 1900;
}

Date.prototype.getTwoDigitMonth = function() {
 return (this.getMonth() < 9) ? '0' + (this.getMonth()+1) : (this.getMonth()+1);
}

Date.prototype.getTwoDigitDate = function() {
 return (this.getDate() < 10) ? '0' + this.getDate() : this.getDate();
}

Date.prototype.getTwoDigitHour = function() {
 return (this.getHours() < 10) ? '0' + this.getHours() : this.getHours();
}

Date.prototype.getTwoDigitMinute = function() {
 return (this.getMinutes() < 10) ? '0' + this.getMinutes() : this.getMinutes();
}

Date.prototype.getTwoDigitSecond = function() {
 return (this.getSeconds() < 10) ? '0' + this.getSeconds() : this.getSeconds();
}

Date.prototype.getISODate = function() {
 return this.getCorrectYear() + '-' + this.getTwoDigitMonth() + '-' + this.getTwoDigitDate();
}

Date.prototype.getHourMinute = function() {
 return this.getTwoDigitHour() + ':' + this.getTwoDigitMinute();
}

Date.prototype.getHourMinuteSecond = function() {
 return this.getTwoDigitHour() + ':' + this.getTwoDigitMinute() + ':' + this.getTwoDigitSecond();
}

//----------------------------------------------------------------------------
//String object extensions
//----------------------------------------------------------------------------
String.prototype.pad_left = function(pad_length, pad_string) {
 var new_string = this;
 for (var i = 0; new_string.length < pad_length; i++) {
     new_string = pad_string + new_string;
 }
 return new_string;
}

//----------------------------------------------------------------------------
//Get the computed style for and element
//----------------------------------------------------------------------------
function getStyle(oElm, strCssRule){
 var strValue = "";
 if(document.defaultView && document.defaultView.getComputedStyle){
     strValue = document.defaultView.getComputedStyle(oElm, "").getPropertyValue(strCssRule);
 }
 else if(oElm.currentStyle){
     strCssRule = strCssRule.replace(/\-(\w)/g, function (strMatch, p1){
         return p1.toUpperCase();
     });
     strValue = oElm.currentStyle[strCssRule];
 }
 return strValue;
}

var SelectBox = {
	    cache: new Object(),
	    init: function(id) {
	        var box = document.getElementById(id);
	        var node;
	        SelectBox.cache[id] = new Array();
	        var cache = SelectBox.cache[id];
	        for (var i = 0; (node = box.options[i]); i++) {
	            cache.push({value: node.value, text: node.text, displayed: 1});
	        }
	    },
	    redisplay: function(id) {
	        // Repopulate HTML select box from cache
	        var box = document.getElementById(id);
	        box.options.length = 0; // clear all options
	        for (var i = 0, j = SelectBox.cache[id].length; i < j; i++) {
	            var node = SelectBox.cache[id][i];
	            if (node.displayed) {
	                box.options[box.options.length] = new Option(node.text, node.value, false, false);
	            }
	        }
	    },
	    filter: function(id, text) {
	        // Redisplay the HTML select box, displaying only the choices containing ALL
	        // the words in text. (It's an AND search.)
	        var tokens = text.toLowerCase().split(/\s+/);
	        var node, token;
	        for (var i = 0; (node = SelectBox.cache[id][i]); i++) {
	            node.displayed = 1;
	            for (var j = 0; (token = tokens[j]); j++) {
	                if (node.text.toLowerCase().indexOf(token) == -1) {
	                    node.displayed = 0;
	                }
	            }
	        }
	        SelectBox.redisplay(id);
	    },
	    delete_from_cache: function(id, value) {
	        var node, delete_index = null;
	        for (var i = 0; (node = SelectBox.cache[id][i]); i++) {
	            if (node.value == value) {
	                delete_index = i;
	                break;
	            }
	        }
	        var j = SelectBox.cache[id].length - 1;
	        for (var i = delete_index; i < j; i++) {
	            SelectBox.cache[id][i] = SelectBox.cache[id][i+1];
	        }
	        SelectBox.cache[id].length--;
	    },
	    add_to_cache: function(id, option) {
	        SelectBox.cache[id].push({value: option.value, text: option.text, displayed: 1});
	    },
	    cache_contains: function(id, value) {
	        // Check if an item is contained in the cache
	        var node;
	        for (var i = 0; (node = SelectBox.cache[id][i]); i++) {
	            if (node.value == value) {
	                return true;
	            }
	        }
	        return false;
	    },
	    move: function(from, to) {
	        var from_box = document.getElementById(from);
	        var to_box = document.getElementById(to);
	        var option;
	        for (var i = 0; (option = from_box.options[i]); i++) {
	            if (option.selected && SelectBox.cache_contains(from, option.value)) {
	                SelectBox.add_to_cache(to, {value: option.value, text: option.text, displayed: 1});
	                SelectBox.delete_from_cache(from, option.value);
	            }
	        }
	        SelectBox.redisplay(from);
	        SelectBox.redisplay(to);
	    },
	    move_all: function(from, to) {
	        var from_box = document.getElementById(from);
	        var to_box = document.getElementById(to);
	        var option;
	        for (var i = 0; (option = from_box.options[i]); i++) {
	            if (SelectBox.cache_contains(from, option.value)) {
	                SelectBox.add_to_cache(to, {value: option.value, text: option.text, displayed: 1});
	                SelectBox.delete_from_cache(from, option.value);
	            }
	        }
	        SelectBox.redisplay(from);
	        SelectBox.redisplay(to);
	    },
	    sort: function(id) {
	        SelectBox.cache[id].sort( function(a, b) {
	            a = a.text.toLowerCase();
	            b = b.text.toLowerCase();
	            try {
	                if (a > b) return 1;
	                if (a < b) return -1;
	            }
	            catch (e) {
	                // silently fail on IE 'unknown' exception
	            }
	            return 0;
	        } );
	    },
	    select_all: function(id) {
	        var box = document.getElementById(id);
	        for (var i = 0; i < box.options.length; i++) {
	            box.options[i].selected = 'selected';
	        }
	    }
	}

/*
SelectFilter2 - Turns a multiple-select box into a filter interface.

Different than SelectFilter because this is coupled to the admin framework.

Requires core.js, SelectBox.js and addevent.js.
*/

function findForm(node) {
    // returns the node of the form containing the given node
    if (node.tagName.toLowerCase() != 'form') {
        return findForm(node.parentNode);
    }
    return node;
}

var SelectFilter = {
    init: function(field_id, field_name, is_stacked, admin_media_prefix) {
        var from_box = document.getElementById(field_id);
        from_box.id += '_from'; // change its ID
        from_box.className = 'filtered';

        // Remove <p class="info">, because it just gets in the way.
        var ps = from_box.parentNode.getElementsByTagName('p');
        for (var i=0; i<ps.length; i++) {
            from_box.parentNode.removeChild(ps[i]);
        }

        // <div class="selector"> or <div class="selector stacked">
        var selector_div = quickElement('div', from_box.parentNode);
        selector_div.className = is_stacked ? 'selector stacked' : 'selector';

        // <div class="selector-available">
        var selector_available = quickElement('div', selector_div, '');
        selector_available.className = 'selector-available';
        quickElement('h2', selector_available, interpolate(gettext('Available %s'), [field_name]));
        var filter_p = quickElement('p', selector_available, '');
        filter_p.className = 'selector-filter';
        quickElement('img', filter_p, '', 'src', admin_media_prefix + 'img/admin/selector-search.gif');
        filter_p.appendChild(document.createTextNode(' '));
        var filter_input = quickElement('input', filter_p, '', 'type', 'text');
        filter_input.id = field_id + '_input';
        selector_available.appendChild(from_box);
        var choose_all = quickElement('a', selector_available, gettext('Choose all'), 'href', 'javascript: (function(){ SelectBox.move_all("' + field_id + '_from", "' + field_id + '_to"); })()');
        choose_all.className = 'selector-chooseall';

        // <ul class="selector-chooser">
        var selector_chooser = quickElement('ul', selector_div, '');
        selector_chooser.className = 'selector-chooser';
        var add_link = quickElement('a', quickElement('li', selector_chooser, ''), gettext('Add'), 'href', 'javascript: (function(){ SelectBox.move("' + field_id + '_from","' + field_id + '_to");})()');
        add_link.className = 'selector-add';
        var remove_link = quickElement('a', quickElement('li', selector_chooser, ''), gettext('Remove'), 'href', 'javascript: (function(){ SelectBox.move("' + field_id + '_to","' + field_id + '_from");})()');
        remove_link.className = 'selector-remove';

        // <div class="selector-chosen">
        var selector_chosen = quickElement('div', selector_div, '');
        selector_chosen.className = 'selector-chosen';
        quickElement('h2', selector_chosen, interpolate(gettext('Chosen %s'), [field_name]));
        var selector_filter = quickElement('p', selector_chosen, gettext('Select your choice(s) and click '));
        selector_filter.className = 'selector-filter';
        quickElement('img', selector_filter, '', 'src', admin_media_prefix + (is_stacked ? 'img/admin/selector_stacked-add.gif':'img/admin/selector-add.gif'), 'alt', 'Add');
        var to_box = quickElement('select', selector_chosen, '', 'id', field_id + '_to', 'multiple', 'multiple', 'size', from_box.size, 'name', from_box.getAttribute('name'));
        to_box.className = 'filtered';
        var clear_all = quickElement('a', selector_chosen, gettext('Clear all'), 'href', 'javascript: (function() { SelectBox.move_all("' + field_id + '_to", "' + field_id + '_from");})()');
        clear_all.className = 'selector-clearall';

        from_box.setAttribute('name', from_box.getAttribute('name') + '_old');

        // Set up the JavaScript event handlers for the select box filter interface
        addEvent(filter_input, 'keyup', function(e) { SelectFilter.filter_key_up(e, field_id); });
        addEvent(filter_input, 'keydown', function(e) { SelectFilter.filter_key_down(e, field_id); });
        addEvent(from_box, 'dblclick', function() { SelectBox.move(field_id + '_from', field_id + '_to'); });
        addEvent(to_box, 'dblclick', function() { SelectBox.move(field_id + '_to', field_id + '_from'); });
        addEvent(findForm(from_box), 'submit', function() { SelectBox.select_all(field_id + '_to'); });
        SelectBox.init(field_id + '_from');
        SelectBox.init(field_id + '_to');
        // Move selected from_box options to to_box
        SelectBox.move(field_id + '_from', field_id + '_to');
    },
    filter_key_up: function(event, field_id) {
        from = document.getElementById(field_id + '_from');
        // don't submit form if user pressed Enter
        if ((event.which && event.which == 13) || (event.keyCode && event.keyCode == 13)) {
            from.selectedIndex = 0;
            SelectBox.move(field_id + '_from', field_id + '_to');
            from.selectedIndex = 0;
            return false;
        }
        var temp = from.selectedIndex;
        SelectBox.filter(field_id + '_from', document.getElementById(field_id + '_input').value);
        from.selectedIndex = temp;
        return true;
    },
    filter_key_down: function(event, field_id) {
        from = document.getElementById(field_id + '_from');
        // right arrow -- move across
        if ((event.which && event.which == 39) || (event.keyCode && event.keyCode == 39)) {
            var old_index = from.selectedIndex;
            SelectBox.move(field_id + '_from', field_id + '_to');
            from.selectedIndex = (old_index == from.length) ? from.length - 1 : old_index;
            return false;
        }
        // down arrow -- wrap around
        if ((event.which && event.which == 40) || (event.keyCode && event.keyCode == 40)) {
            from.selectedIndex = (from.length == from.selectedIndex + 1) ? 0 : from.selectedIndex + 1;
        }
        // up arrow -- wrap around
        if ((event.which && event.which == 38) || (event.keyCode && event.keyCode == 38)) {
            from.selectedIndex = (from.selectedIndex == 0) ? from.length - 1 : from.selectedIndex - 1;
        }
        return true;
    }
}
