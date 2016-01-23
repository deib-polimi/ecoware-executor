$(document).ready(function () {
  'use strict';

  $.get('/api/vm', function(data) {
    $.each(data, function(i, vm) {
      var $row = $('<tr>');
      var td = $('<td>').text(vm.id).appendTo($row);
      $('<td>').text(vm.name).appendTo($row);
      $('<td>').text(vm.cpu_cores).appendTo($row);
      $('<td>').text(vm.mem_units).appendTo($row);
      $('<td>').text(vm.docker_port).appendTo($row);
      $row.appendTo($('#vms'));
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
      $.post('/api/vm/create', data, function(resp) {
        toastr.success('VM {} is created (time={}s'.format(data.name, 60));
        $btn.button('reset');
      }).fail(function() {
        toastr.error('Error creating VM')
        console.error('Error creating VM')
        $btn.button('reset');
      });
    }
  });
});