/* jshint globalstrict: true */
'use strict';

describe('hz.widget.modal module', function(){
  it('should have been defined', function(){
    expect(angular.module('hz.widget.modal')).toBeDefined();
  });
});

describe('modal factory', function(){

  var modal;
  var modalData = {
    title: 'Confirm deletion',
    body: 'Are you sure?',
    submit: 'Yes',
    cancel: 'No'
  };

  beforeEach(module('ui.bootstrap'));
  beforeEach(module('hz'));
  beforeEach(module('hz.widgets'));
  beforeEach(module('hz.widget.modal'));
  beforeEach(inject(function($injector, simpleModalService){
    modal = simpleModalService;
  }));

  it('should fail without any params', function(){
    expect(modal()).toBeUndefined();
  });

  it('should fail without a title', function(){
    var data = angular.copy(modalData);
    delete data.title;
    expect(modal(data)).toBeUndefined();
  });

  it('should fail without a body', function(){
    var data = angular.copy(modalData);
    delete data.body;
    expect(modal(data)).toBeUndefined();
  });

  it('should have default submit and cancel labels', function(){
    var data = angular.copy(modalData);
    delete data.submit;
    delete data.cancel;
    expect(modal(data)).toBeDefined();
  });

  it('should work when all params are supplied', function(){
    var data = angular.copy(modalData);
    expect(modal(data)).toBeDefined();
  });

});
