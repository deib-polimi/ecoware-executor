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
});