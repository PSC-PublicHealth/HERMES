;(function($) {
    $.widget("hierarchical.barchart", {
        options: {
            file: "static/hierarchical-charts/hierarchical-barchart-testdata.json",
            minWidth: 800,
            minHeight: 300,
            scrollable: true,
            resizable: true,
            hasChildrenColor: "steelblue",
            noChildrenColor: "#adf",
            trant: {
                title: 'Hierarchical Barchart'
            }
        },

        _resize_container: function(total_height) {
            // sets the widgets svg height and the clickable background to the total
            // height of all of the stacked bars
            this.background.attr("height", total_height);
            this.svg.attr("height", total_height); 
        },

        _create: function() {
            trant = this.options.trant;

            this.containerID = $(this.element).attr('id');
            $(this.element).css({
                float: "left"
            });
            
            this.svgContainerID = this.containerID+"svgContainer";
            
            d3.select("#"+this.containerID).append("div")
                .attr("id", this.svgContainerID)
                .attr("height", 200);
   
            var jsonDataURL = this.options.jsonDataURLBase + "?"
                            + this.options.jsonDataURLParameters.join("&");
    
            $("<link/>", {
               rel: "stylesheet",
               type: "text/css",
               href: "static/hierarchical-charts/hierarchical-barcharts.css"
            }).appendTo("head");
    
            var margin = {top: 30, right: 120, bottom: 0, left: 120};
            var width = this.options.minWidth - margin.left - margin.right;
            var height = this.options.minHeight - margin.top - margin.bottom;
        
            var x = d3.scale.linear()
                .range([0, width]);
        
            var barHeight = 20;
        
            var color = d3.scale.ordinal()
                .range([this.options.hasChildrenColor,
                        this.options.noChildrenColor]);
        
            var duration = 750,
                delay = 25;
        
            var partition = d3.layout.partition()
                .value(function(d) { return d.size; });
        
            var xAxis = d3.svg.axis()
                .scale(x)
                .orient("top");
        
            var svgTitle = d3.select("#"+this.svgContainerID).append("div")
                .attr("id", "title")
                .attr("text-align", "center")
                .text(trant['title']);

            var svg = d3.select("#"+this.svgContainerID).append("svg")
                .attr("class", "hierarchicalBarchart")
                .attr("width", width + margin.left + margin.right)
                .attr("height", height + margin.top + margin.bottom);
 
            this.svg = svg;
           
            var svg_g = svg.append("g")
                .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

            var bkg = svg_g.append("rect")
                .attr("class", "background")
                .attr("width", width)
                .attr("height", height)
                .on("click", up);

            this.background = bkg;
        
            svg_g.append("g")
                .attr("class", "x axis");
        
            svg_g.append("g")
                .attr("class", "y axis")
                .append("line")
                .attr("y1", "100%");

            if (this.options.resizable) {
                // jquery
                $("#"+this.svgContainerID).css("padding","10px");
                $("#"+this.svgContainerID).css("margin","5px");
            }
   
            if (this.options.scrollable) {
                // jquery
                $("#"+this.containerID).css({
                    overflow: "scroll",
                    height: "" + this.options.minHeight + "px"
                });
            }

            var currency = "USD";
            var currency_year = 2010;

            d3.json(jsonDataURL, function(error, ret) {
                if (error) {console.log(ret.error);}
                //console.log(ret.data);
                var root = ret.data.cost_summary;
                currency = ret.data.currency_base;
                currency_year = ret.data.currency_year; 
                partition.nodes(root);
                x.domain([0, root.value]).nice();
                down(root, 0);
            });

            svgTitle.append("div").append("text")
                .attr("class", "x label")
                .attr("text-anchor", "end")
                .attr("x", width)
                .attr("y", height - 6)
                .text(trant['currency_label'] + ': ' + currency + ", " + 
                        trant['year_label'] + ': ' + currency_year);
          
            var _widget = this;

            // down function called to decend into a selected bar on click
            function down(d, i) {
                if (!d.children || this.__transition__) return;
                var end = duration + d.children.length * delay;
        
                // Mark any currently-displayed bars as exiting.
                var exit = svg_g.selectAll(".enter")
                    .attr("class", "exit");
        
                // Entering nodes immediately obscure the clicked-on bar, so hide it.
                exit.selectAll("rect").filter(function(p) { return p === d; })
                    .style("fill-opacity", 1e-6);
        
                // Enter the new bars for the clicked-on data.
                // Per above, entering bars are immediately visible.
                var enter = bar(d)
                    .attr("transform", stack(i))
                    .style("opacity", 1);
        
                // Have the text fade-in, even though the bars are visible.
                // Color the bars as parents; they will fade to children if appropriate.
                enter.select("text").style("fill-opacity", 1e-6);
                enter.select("rect").style("fill", color(true));
        
                // Update the x-scale domain.
                x.domain([0, d3.max(d.children, function(d) { return d.value; })]).nice();
        
                // Update the x-axis.
                svg_g.selectAll(".x.axis").transition()
                    .duration(duration)
                    .call(xAxis);
       
                var total_height = (2 * (margin.top + margin.bottom)) + (barHeight * 1.2);

                // Transition entering bars to their new position.
                var enterTransition = enter.transition()
                    .duration(duration)
                    .delay(function(d, i) { return i * delay; })
                    .attr("transform", function(d, i) {
                        var this_bar_height = barHeight * i * 1.2;
                        total_height += (1.2 * barHeight);
                        return "translate(0," + barHeight * i * 1.2 + ")";
                    });

                _widget._resize_container(total_height);
        
                // Transition entering text.
                enterTransition.select("text")
                    .style("fill-opacity", 1);
        
                // Transition entering rects to the new x-scale.
                enterTransition.select("rect")
                    .attr("width", function(d) { return x(d.value); })
                    .style("fill", function(d) { return color(!!d.children); });
        
                // Transition exiting bars to fade out.
                var exitTransition = exit.transition()
                    .duration(duration)
                    .style("opacity", 1e-6)
                    .remove();
        
                // Transition exiting bars to the new x-scale.
                exitTransition.selectAll("rect")
                    .attr("width", function(d) { return x(d.value); });
        
                // Rebind the current node to the background.
                svg_g.select(".background")
                    .datum(d)
                    .transition()
                    .duration(end);

                d.index = i;
            };
       
            // up function called to pop back up a level when background
            // is clicked
            function up(d) {
                if (!d.parent || this.__transition__) return;
                var end = duration + d.children.length * delay;
        
                // Mark any currently-displayed bars as exiting.
                var exit = svg_g.selectAll(".enter")
                    .attr("class", "exit");
 
                var total_height = (2 * (margin.top + margin.bottom)) + (barHeight * 1.2);
       
                // Enter the new bars for the clicked-on data's parent.
                var enter = bar(d.parent)
                    .attr("transform", function(d, i) {
                        total_height += (1.2 * barHeight);
                        return "translate(0," + barHeight * i * 1.2 + ")";
                    })
                    .style("opacity", 1e-6);
 
                _widget._resize_container(total_height);
        
                // Color the bars as appropriate.
                // Exiting nodes will obscure the parent bar, so hide it.
                enter.select("rect")
                    .style("fill", function(d) { return color(!!d.children); })
                    .filter(function(p) { return p === d; })
                    .style("fill-opacity", 1e-6);
        
                // Update the x-scale domain.
                x.domain([0, d3.max(d.parent.children, function(d) {
                        return d.value; 
                    })])
                    .nice();
        
                // Update the x-axis.
                svg_g.selectAll(".x.axis").transition()
                    .duration(duration)
                    .call(xAxis);
        
                // Transition entering bars to fade in over the full duration.
                var enterTransition = enter.transition()
                    .duration(end)
                    .style("opacity", 1);
        
                // Transition entering rects to the new x-scale.
                // When the entering parent rect is done, make it visible!
                enterTransition.select("rect")
                    .attr("width", function(d) { return x(d.value); })
                    .each("end", function(p) {
                        if (p === d) {
                            d3.select(this).style("fill-opacity", null);
                        }
                    });
        
                // Transition exiting bars to the parent's position.
                var exitTransition = exit.selectAll("g").transition()
                    .duration(duration)
                    .delay(function(d, i) { return i * delay; })
                    .attr("transform", stack(d.index));
        
                // Transition exiting text to fade out.
                exitTransition.select("text")
                    .style("fill-opacity", 1e-6);
        
                // Transition exiting rects to the new scale and fade to parent color.
                exitTransition.select("rect")
                    .attr("width", function(d) { return x(d.value); })
                    .style("fill", color(true));
        
                // Remove exiting nodes when the last child has finished transitioning.
                exit.transition()
                    .duration(end)
                    .remove();
        
                // Rebind the current parent to the background.
                svg_g.select(".background")
                    .datum(d.parent)
                    .transition()
                    .duration(end);

            };
        
            // Creates a set of bars for the given data node, at the specified index.
            function bar(d) {
                var bar = svg_g.insert("g", ".y.axis")
                    .attr("class", "enter")
                    .attr("transform", "translate(0,5)")
                    .selectAll("g")
                    .data(d.children)
                    .enter().append("g")
                    .style("cursor", function(d) {
                        return !d.children ? null : "pointer";
                    })
                    .on("click", down);
        
                bar.append("text")
                    .attr("x", -6)
                    .attr("y", barHeight / 2)
                    .attr("dy", ".35em")
                    .style("text-anchor", "end")
                    .text(function(d) { return d.name; });
        
                bar.append("rect")
                    .attr("width", function(d) { return x(d.value); })
                    .attr("height", barHeight);
        
                return bar;
            };
        
            // A stateful closure for stacking bars horizontally.
            function stack(i) {
                var x0 = 0;
                return function(d) {
                    var tx = "translate(" + x0 + "," + barHeight * i * 1.2 + ")";
                    x0 += x(d.value);
                    return tx;
                };
            };
        }
    });
})(jQuery);

