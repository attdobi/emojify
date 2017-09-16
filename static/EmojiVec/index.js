
//initiallize search window to past 1 month
window['range']=moment().subtract(60, 'days').format('MMMM D, YYYY, HH, mm') + ' - ' + moment().format('MMMM D, YYYY, HH, mm')

// the table rows
    // column definitions
  var columns = [
                  {head: 'Rank', dataKey: 'rank'},
                  {head: 'Emoji', dataKey: 'label'},
                  {head: 'Cosine Sim', dataKey: 'str_value'},
  ];


//Update and make pie chart 

    var URL_BASE = "/_emojivec";

function update_url() {
  return URL_BASE +"?word=" + document.getElementById("word").value ;
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

function make_graph() {
  url = update_url()
  
  d3.json(url, function(error, data) {
    var fmt = d3.format("d");
    nv.addGraph(function() {
        var chart = nv.models.pieChart();
        chart.margin({top: 30, right: 60, bottom: 20, left: 20});
        
        var datum = data.values;
        //var datum = data_piechart;

        chart.color(d3.scale.category20c().range());

    chart.tooltipContent(function(key, y, e, graph) {
          var x = String(key);
          var y =  String(y);
         //var yy= +y.replace(/,/g, ''); //remove the comma and make yy an int with + 
         //var yper = String(yper)
         //old: var yy= parseInt(y.replace(/,/g, ''))
              
              //tooltip_str = '<center><b>'+x+'</b></center>' +'<center>'+ commaSeparateNumber(yy)+'</center>' +  d3.format(".1%")(yy/ysum);
              tooltip_str = '<center><b>'+x+'</b></center>' +'<center>'+ y+'</center>' ;
              return tooltip_str;
              });
        chart.showLabels(true);

            chart.donut(false);

       chart.showLegend(true);

        chart
            .x(function(d) { return d.label })
            .y(function(d) { return d.value });
            //y data is saved with commas at 1000 for the table format. Remove commas:
            //.y(function(d) { return d.value.replace(/,/g, ''); });

        chart.width(600);

        chart.height(600);

            d3.select('#piechart svg')
            .datum(datum)
            .transition().duration(500)
            .attr('width', 600)
            .attr('height', 600)
            .style({"font-size": "50px"})
            .call(chart);
        
            //increase fontsize
            d3.selectAll(".nv-label text")
            .attr("text-anchor", "middle")
            .style({"font-family": 'Apple Color Emoji'});
            //.style({"-webkit-transform": "scale(2)"});
            //.style({"font-size": "50px"})
            //.attr('transform', 'scale(1.5) translate(-5,0)');
            
            //select legend
            d3.selectAll(".nv-legendWrap")
            .style({"font-size": "20px"})
            .style({"font-family": 'Apple Color Emoji'});
            
  
        
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
    });
}
make_graph();
