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
    $.post('/api/plan/translate', data, function(resp) {
      $('#actions-area').val(JSON.stringify(resp, null, 2));
      $.post('/api/plan/preview', data, function(preview) {
        $('#preview-topology').val(JSON.stringify(preview, null, 2));
      });
    });
  });

  $('#execute-btn').click(function() {
    var data = $('#plan-area').val();
    $.post('/api/plan/execute', data, function(resp) {
      console.log(resp)
    });
  });

  $.get('/api/topology', function(data) {
    $('#current-topology').val(JSON.stringify(data, null, 2));
  });

});