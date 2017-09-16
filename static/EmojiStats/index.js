//initiallize search window to past 1 month
window['range']=moment().subtract(60, 'days').format('MMMM D, YYYY, HH, mm') + ' - ' + moment().format('MMMM D, YYYY, HH, mm')

        
//Update and make table
var URL_BASE = "/dbstats";
// Update graph in response to inputs 
 d3.select("#search_type").on("input", function(d) {
  click_box(d);
  make_graph(d);
  });//call two functions
 d3.select("#user_lang").on("input", make_graph);
 d3.select("#freq_filter").on("input", make_graph);
 d3.select("#face_filter").on("input", make_graph);
 d3.select("#sort_type").on("input", make_graph);
 d3.select("#cbox1").on("click", make_graph);
  //d3.select("#reportrange").on("click", make_graph);//doesn't work on menu click, function is called in JS at top
    
function click_box() {
        if(document.getElementById("search_type").value=="skin"){
        document.getElementById("cbox1").checked=1;}
        else{
        document.getElementById("cbox1").checked=0;}
}

// Return url to recieve csv data with query filled in from input fields
function update_url() {
  return URL_BASE +"?word=" + document.getElementById("word").value +
            "&search_type=" + document.getElementById("search_type").value +
            "&user_lang=" + document.getElementById("user_lang").value +
            "&freq_filter=" + document.getElementById("freq_filter").value + 
            "&face_filter=" + document.getElementById("face_filter").value +
            "&sort_type=" + document.getElementById("sort_type").value +
            "&date_range=" + window['range'] ;
}

function commaSeparateNumber(val){
    while (/(\d+)(\d{3})/.test(val.toString())){
      val = val.toString().replace(/(\d+)(\d{3})/, '$1'+','+'$2');
    }
    return val;
  }
  
function add(a, b) {
    return a + b;
}

function defColumns() {
// the table rows
    // column definitions
    var Group='zone';
    if(document.getElementById("sort_type").value=="Language"){
        Group='lang'
    }

    if(document.getElementById("cbox1").checked){
        var columns = [
                        {head: Group, dataKey: Group},
                        {head: 'Top Emojis', dataKey: 'emojis'},
                        {head: '%', dataKey: 'percent'},
                      ];
    }
    else
    {   
        var columns = [
                        {head: Group, dataKey: Group},
                        {head: 'Top Emojis', dataKey: 'emojis'},
                      ];
    }
    return columns
}

function make_graph() {
  url = update_url();
  columns=defColumns();
  d3.json(url, function(error, data) {
    
        var datum = data.values;
        //var datum = data_piechart;
  
        
// create table
    //Clear previous table
    d3.selectAll("#table > *").remove();
    //var table = d3.select('#table');
     
  var sortAscending = true;
  //var table = d3.select('#page-wrap').append('table');
  var table = d3.select('#table');
  // Can use the keys for the json data, only if they are stored as an ordered dict.
  // Else use mapping of the column header to the key.
  //var titles = d3.keys(datum[0]);
  var headers = table.append('thead').append('tr')
                   .selectAll('th')
                   .data(columns).enter()
                   .append('th')
                   .text(function (d) {
                      return d.head;
                    })
                   // NOTE: The .replace(/,/g, '') is to remove the comma from the count stirng
                   // when sorting. This code would be a lot cleaner without the need to remove the comma.
                   .on('click', function (d) {
                     headers.attr('class', 'header');
                     if (sortAscending) {
                       rows.sort((a, b) => {
                        if (d.dataKey != 'value') {
                          return a[d.dataKey] - b[d.dataKey];
                          } 
                        else {
                          return a[d.dataKey].replace(/,/g, '') - b[d.dataKey].replace(/,/g, '');
                          }
                        });
                       sortAscending = false;
                       this.className = 'aes';
                     } 
                     else {
                     rows.sort((a, b) => {
                        if (d.dataKey != 'value') {
                          return b[d.dataKey] - a[d.dataKey];
                          } 
                        else {
                          return b[d.dataKey].replace(/,/g, '') - a[d.dataKey].replace(/,/g, '');
                          }
                        });
                     sortAscending = true;
                     this.className = 'des';
                     }
                     
                   });

  var rows = table.append('tbody').selectAll('tr')
               .data(datum).enter()
               .append('tr');
  rows.selectAll('td')
    .data(function (d) {
      return columns.map(k => {
        return { 'value': d[k.dataKey], 'name': k.dataKey};
      });
    }).enter()
    .append('td')
    .attr('data-th', function (d) {
      return d.name;
    })
    .text(function (d) {
      return d.value;
    });
        
  });
}

make_graph();
