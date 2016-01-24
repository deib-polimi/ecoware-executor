(function() {

   var onVmCreate = function() {
    var $btn = $(this);
    $btn.button('loading');
    var data = {
      name: $('#vm-name-input').val(),
      cpu_cores: $('#vm-cpu-input').val(),
      mem_units: $('#vm-mem-input').val()
    };
    $.ajax({
      url: '/api/vm', 
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(data), 
      success: function(resp) {
        $btn.button('reset');
        $('#add-vm-modal').modal('hide');
        toastr.success('VM {0} is created (time={1}s)'.format(resp.name, resp.time));
        insert_row(resp);
      },
      error: function() {
        $btn.button('reset');
        toastr.error('Error creating VM')
        console.error('Error creating VM')
      }
    });
  };

  var onVmDelete = function() {};
  var onVmStop = function() {};
  var onVmStart = function() {};

  var insert_row = function(container) {
    var $row = $('<tr>');
    var td = $('<td>').text(container.id).appendTo($row);
    $('<td>').text(container.vm.name).appendTo($row);
    $('<td>').text(container.name).appendTo($row);
    $('<td>').text(container.cpuset).appendTo($row);
    $('<td>').text('{0} ({1}gb)'.format(container.mem_units, container.mem)).appendTo($row);
    var $btnGroup = $('<div>').addClass('btn-group');
    $('<button>').addClass('btn btn-default').text('Delete').click(onVmDelete).appendTo($btnGroup);
    $('<button>').addClass('btn btn-default').text('Stop').click(onVmStop).appendTo($btnGroup);
    $('<button>').addClass('btn btn-default').text('Start').click(onVmStart).appendTo($btnGroup);
    $('<td>').append($btnGroup).appendTo($row);
    $row.appendTo($('#containers'));
    $row.data('container', container);
  };

  $(document).ready(function () {
    'use strict';

    $.get('/api/vm', function(data) {
      $.each(data, function(i, vm) {
        console.log(vm)
        $.each(vm.containers, function(j, container) {
          console.log(container)
          container.vm = vm;
          insert_row(container);
        });
      });
    });
  });

})();
