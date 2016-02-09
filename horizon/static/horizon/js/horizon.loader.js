/*
 Simple loader rendering logic
 */

horizon.loader = {
  templates: {
    inline: '#loader-inline',
    modal: '#loader-modal'
  }
};

horizon.loader.inline = function(text) {
  return horizon.templates.compile(horizon.loader.templates.inline, {text: text});
};

horizon.loader.modal = function(text) {
  return horizon.templates.compile(horizon.loader.templates.modal, {text: text});
};

