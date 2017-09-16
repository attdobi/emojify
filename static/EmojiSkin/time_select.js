$(function() {
  function cb(start, end) {
      $('#reportrange span').html(start.format('MMMM D, YYYY') + ' - ' + end.format('MMMM D, YYYY'));
      window['range'] = start.format('MMMM D, YYYY, HH, mm') + ' - ' + end.format('MMMM D, YYYY, HH, mm')
      make_graph() //call make_graph function
     // $.getJSON('/_report_range', {
     //daterange:start.format('MMMM D, YYYY, HH') + ' - ' + end.format('MMMM D, YYYY, HH')});
  }
  cb(moment().subtract(60, 'days'), moment());
  $('#reportrange').daterangepicker({
      timePicker: true,
      timePickerIncrement: 30,
      ranges: {
         'Today': [ moment().subtract(1, 'days').endOf('day'), moment()],
         'Yesterday': [ moment().subtract(2, 'days').endOf('day'), moment().subtract(1, 'days').endOf('day')],
         'Last Hour': [moment().subtract(1, 'hours'), moment()],
         'Last 7 Days': [moment().subtract(6, 'days'), moment()],
         'Last 30 Days': [moment().subtract(29, 'days'), moment()],
         'This Month': [moment().startOf('month'), moment().endOf('month')],
         'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')],
         'Last Year':[moment().subtract(1, 'year'), moment()]
      }
  }, cb);
});