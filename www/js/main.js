(function() {

  var onVmDelete = function() {
    var $row = $(this).closest('tr');
    var vm = $row.data('vm');
    var $btn = $(this).button('loading');
    $.ajax('/api/vm/{0}'.format(vm.id), {
      method: 'DELETE',
      success: function(data) {
        $btn.button('reset');
        $row.remove();
        toastr.success('VM "{0}" is deleted in {1}s'.format(vm.name, data.time));
      },
      error: function() {
        $btn.button('reset');
        toastr.error('Error deleting vm');
        console.error('Error deleting vm');
      }
    });
  };

  var onVmStop = function() {
    var vm = $(this).closest('tr').data('vm');
    var $btn = $(this).button('loading');
    $.post('/api/vm/{0}/stop'.format(vm.id), function(data) {
      $btn.button('reset');
      toastr.success('VM "{0}" is stopped in {1}s'.format(vm.name, data.time));
    }).fail(function() {
      $btn.button('reset');
      toastr.error('Error stopping vm');
      console.error('Error stopping vm');
    });
  };

  var onVmStart = function() {
    var vm = $(this).closest('tr').data('vm');
    var $btn = $(this).button('loading');
    $.post('/api/vm/{0}/start'.format(vm.id), function(data) {
      $btn.button('reset');
      toastr.success('VM "{0}" is started in {1}s'.format(vm.name, data.time));
    }).fail(function() {
      $btn.button('reset');
      toastr.error('Error starting vm');
      console.error('Error starting vm');
    });
  };

  var onVmCreate = function() {
    var $btn = $(this);
    $btn.button('loading');
    var data = {
      name: $('#vm-name-input').val(),
      cpu_cores: parseInt($('#vm-cpu-input').val()),
      mem_units: parseInt($('#vm-mem-input').val()),
      host: $('#vm-host-input').val()
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
        toastr.error('Error creating VM');
        console.error('Error creating VM');
      }
    });
  };

  var insert_row = function(vm) {
    var $row = $('<tr>');
    var td = $('<td>').text(vm.id).appendTo($row);
    $('<td>').text(vm.name).appendTo($row);
    $('<td>').text(vm.cpu_cores).appendTo($row);
    $('<td>').text('{0} ({1}gb)'.format(vm.mem_units, vm.mem)).appendTo($row);
    var dockerAddr = '{0}:{1}'.format(vm.host, vm.docker_port);
    $('<td>').text(dockerAddr).appendTo($row);
    var $btnGroup = $('<div>').addClass('btn-group');
    $('<button>').addClass('btn btn-default').text('Delete').click(onVmDelete).appendTo($btnGroup);
    $('<button>').addClass('btn btn-default').text('Stop').click(onVmStop).appendTo($btnGroup);
    $('<button>').addClass('btn btn-default').text('Start').click(onVmStart).appendTo($btnGroup);
    $('<td>').append($btnGroup).appendTo($row);
    $row.appendTo($('#vms'));
    $row.data('vm', vm);
  };

  $(document).ready(function () {
    'use strict';

    $.get('/api/vm', function(data) {
      $.each(data, function(i, vm) {
        insert_row(vm);
      });
    });

    $('#create-vm-btn').click(function() {
      var isValid = $('#add-vm-form')[0].checkValidity();
      if (!isValid) {
        $('#add-vm-form').find(':submit').click();
      } else {
        onVmCreate.call(this);
      }
    });
  });

})();
