$(document).ready(function() {

  var plan = {
    'jboss': {
      'cpu_cores': 2,
      'mem': 1
    },
    'db': {
      'cpu_cores': 1,
      'mem': 2
    }
  };
  $('#plan-area').val(JSON.stringify(plan, null, 2));

  $('#preview-btn').click(function() {
    var data = $('#plan-area').val();
    $.post('/', data, function(resp) {
      var data = JSON.parse(resp);
      $('#actions-area').val(JSON.stringify(data, null, 2));
    });
  });

});