// The base endpoint to receive data from. See update_url()

var URL_BASE = "http://localhost:5000/db/";

// Update graph in response to inputs 
//this updates continuously as text is entered
//d3.select("#word").on("input", make_graph);

// Return url to recieve csv data with query filled in from input fields
function update_url() {
  return URL_BASE +"?word=" + document.getElementById("word").value;
}
    
function make_graph() {
  url = update_url()
  
  d3.json(url, function(error, data) {

    nv.addGraph(function() {
        var chart = nv.models.pieChart();
        chart.margin({top: 30, right: 60, bottom: 20, left: 60});
        var datum = data.values;
        //var datum = data_piechart;

        chart.color(d3.scale.category20c().range());

    chart.tooltipContent(function(key, y, e, graph) {
          var x = String(key);
              var y =  String(y) +'';

              tooltip_str = '<center><b>'+x+'</b></center>' + y;
              return tooltip_str;
              });
        chart.showLabels(true);

            chart.donut(false);

       chart.showLegend(true);

        chart
            .x(function(d) { return d.label })
            .y(function(d) { return d.value });

        chart.width(600);

        chart.height(600);


            d3.select('#piechart svg')
            .datum(datum)
            .transition().duration(500)
            .attr('width', 600)
            .attr('height', 600)
            .call(chart);
        
            //increase fontsize
            d3.selectAll(".nv-label text")
            .attr("text-anchor", "middle")
            .style({"font-size": "50px"});
            //.attr('transform', 'scale(1.5) translate(-5,0)');
            
            //select legend
            d3.selectAll(".nv-legendWrap")
            .style({"font-size": "50px"});
        });
    });
    
}
make_graph();
