if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this.replace(/{(\d+)}/g, function(match, number) {
      return typeof args[number] != 'undefined'
        ? args[number]
        : match
      ;
    });
  };
}

$(document).ready(function () {
  'use strict';

  var insert_row = function(vm) {
    var $row = $('<tr>');
    var td = $('<td>').text(vm.id).appendTo($row);
    $('<td>').text(vm.name).appendTo($row);
    $('<td>').text(vm.cpu_cores).appendTo($row);
    $('<td>').text('{0} ({1}gb)'.format(vm.mem_units, vm.mem)).appendTo($row);
    $('<td>').text(vm.docker_port).appendTo($row);
    var $btn = $('<button>').addClass('btn btn-default').text('Delete').click(function() {
      var $row = $(this).closest('tr');
      var vm = $row.data('vm');
      var $btn = $(this).button('loading');
      $.ajax('/api/vm/{0}'.format(vm.id), {
        method: 'DELETE',
        success: function(data) {
          $btn.button('reset');
          $row.remove();
          toastr.success('VM "{0}" is deleted in {1}s'.format(vm.name, data.time))
        },
        error: function() {
          $btn.button('reset');
          toastr.error('Error deleting vm');
          console.error('Error deleting vm');
        }
      });
    });
    $('<td>').append($btn).appendTo($row);
    $row.appendTo($('#vms'));
    $row.data('vm', vm);
  };

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
    }
  });
});