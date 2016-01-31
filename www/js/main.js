(function() {

  $(document).ready(function () {
    'use strict';
    $.get('/api/topology', function(resp) {
      var json = JSON.stringify(resp, null, '\t');
      $('#plan-area').text(json);
    });
  });

})();
