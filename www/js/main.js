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
  $('#input-plan').val(JSON.stringify(plan, null, 2));

});