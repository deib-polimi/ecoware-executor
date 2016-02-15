(function() {

  function sendPlan($btn) {
    var data = JSON.parse($('#plan-area').val());
    $.ajax('/api/plan', {
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify(data),
      success: function(resp) {
        $btn.button('reset');
        toastr.success('Plan is processed successfully in {0}s'.format(resp.time));
      },
      error: function() {
        $btn.button('reset');
        toastr.error('Error processing this plan');
      }
    });
  };

  $(document).ready(function () {
    'use strict';
    $.get('/api/topology', function(resp) {
      var json = JSON.stringify(resp, null, '\t');
      $('#tier-area').text(json);
    });

    $.get('/api/allocation', function(resp) {
      var json = JSON.stringify(resp, null, '\t');
      $('#plan-area').text(json);
    });

    $('#process-plan-btn').click(function() {
      var $btn = $(this).button('loading');
      var data = JSON.parse($('#tier-area').val());
      $.ajax('/api/topology', {
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: function(resp) {
          sendPlan($btn);
        },
        error: function() {
          $btn.button('reset');
          toastr.error('Error processing topology description');
        }
      });
    });
  });

})();
