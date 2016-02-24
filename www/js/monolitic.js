(function() {

  function sendPlan($btn) {
    var data = JSON.parse($('#plan-area').val());
    $.ajax('/api/monolitic/executor', {
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(data),
      success: function(resp) {
        $btn.button('reset');
        if (resp.error) {
          toastr.error('Error processing this plan: ' + resp.error);
        } else {
          console.log(resp)
          var json = JSON.stringify(resp, null, '\t');
          console.log(json)
          $('#plan-area').val(json);
          toastr.success('Plan is processed successfully in {0}s'.format(resp.time));
        }
        
      },
      error: function() {
        $btn.button('reset');
        toastr.error('Error processing this plan');
      }
    });
  };

  $(document).ready(function () {
    'use strict';
    $.get('/api/monolitic/topology', function(resp) {
      var json = JSON.stringify(resp, null, '\t');
      $('#tier-area').val(json);
    });

    $.get('/api/monolitic/allocation', function(resp) {
      var json = JSON.stringify(resp, null, '\t');
      $('#allocation-area').val(json);
    });

    $('#process-plan-btn').click(function() {
      var $btn = $(this).button('loading');
      var data = JSON.parse($('#tier-area').val());
      $.ajax('/api/monolitic/topology', {
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function(resp) {
          // sendPlan($btn);
          alert('ok')
        },
        error: function() {
          $btn.button('reset');
          toastr.error('Error processing topology description');
        }
      });
    });
  });

})();
