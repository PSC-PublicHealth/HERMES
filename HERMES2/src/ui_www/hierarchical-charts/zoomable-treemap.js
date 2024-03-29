/*
*/
;(function($) {
    $.widget("hierarchical.treemap", {
        options: {
            file: "static/hierarchical-charts/zoomable-treemap-testdata.json",
    minWidth: 800,
    minHeight: 300,
    scrollable: true,
    resizable: true,
    hasChildrenColor: "steelblue",
    noChildrenColor: "#adf",
    trant: {
        title: 'Zoomable Treemap'
    }
        },


    _format_currency: function(d) {
        var cost_string = "No Cost Data Availalble"
        if ($.isNumeric(d.value) && d.value > 0.0) {
            cost_string = parseFloat(d.value, 10).toFixed(2).replace(/(\d)(?=(\d{3})+\.)/g, "$1,").toString();
            cost_string += " (" + this.currency_year + " " + this.currency + ")";
        }
        else {
            console.log("Error parsing cost for " + d.name + "!" + "  Value supplied is: " + d.value);
        }
        return cost_string;
    },

    _create: function() {
        // TRAnslated Text
        this.trant = this.options.trant;

        this.containerID = $(this.element).attr('id');

        $(this.element).css({
            float: "left"
        });

        this.svgContainerID = this.containerID+"svgContainer";

        d3.select("#"+this.containerID).append("svgcontainer")
            .attr("id", this.svgContainerID)
            .attr("class","ztm");
        console.log(this.containerID);
        console.log(this.svgContainerID);
        this.jsonDataURL = this.options.jsonDataURLBase + "?"
            + this.options.jsonDataURLParameters.join("&");

        $("<link/>", {
            rel: "stylesheet",
            type: "text/css",
            href: "static/hierarchical-charts/zoomable-treemap.css"
        }).appendTo("head");

        var _this = this;
        // bind this instance's refresh method to the window resize event
        // wrap in function closure
        window.addEventListener('resize', function(e) {
            _this.refresh();
        });

        this.refresh();
    },

    refresh: function() {
        $("#"+this.svgContainerID).empty();
        this.draw();
    },

    draw: function() {

        var _widgit = this;

        console.log("refreshing treemap");
        // calculation of width should actually take margins & padding into account.
        // the scaling factor used below is a temporary solution simply because I've
        // endured enough tedious box model arithmetic for one day
        var margin = {top: 20, right: 0, bottom: 0, left: 0},
            width = $(this.element).parent().parent().width() * .97,
            height = 500 - margin.top - margin.bottom,
            formatNumber = d3.format(",d"),
            transitioning;

        var x = d3.scale.linear()
            .domain([0, width])
            .range([0, width]);

        var y = d3.scale.linear()
            .domain([0, height])
            .range([0, height]);

        var treemap = d3.layout.treemap()
            .children(function(d, depth) { return depth ? null : d._children; })
            .sort(function(a, b) { return a.value - b.value; })
            .ratio(height / width * 0.5 * (1 + Math.sqrt(5)))
            .round(false);

        var svgTitle = d3.select("#"+this.svgContainerID).append("div")
            .attr("id", "title")
            .attr("text-align", "center")
            .style("margin-top", "20px")
            .style("margin-bottom", "10px")
            .text(this.trant['title']);

        var svg = d3.select("#"+this.svgContainerID).append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.bottom + margin.top)
            .style("margin-left", -margin.left + "px")
            .style("margin-right", -margin.right + "px")
            .append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")")
            .style("shape-rendering", "crispEdges");

        _widgit.parent_title_div = d3.select("#"+this.svgContainerID).append("div")
            .attr("id", "parent_title_div")
            .style("margin-top", "20px")
            .style("margin-bottom", "10px")
            .attr("width", "100%")
            .html("&nbsp");

        _widgit.child_title_div = d3.select("#"+this.svgContainerID).append("div")
            .attr("id", "child_title_div")
            .style("margin-bottom", "20px")
            .attr("width", "100%")
            .html("&nbsp");

        var grandparent = svg.append("g")
            .attr("class", "grandparent");

        grandparent.append("rect")
            .attr("y", -margin.top)
            .attr("width", width)
            .attr("height", margin.top);

        grandparent.append("text")
            .attr("x", 6)
            .attr("y", 6 - margin.top)
            .attr("dy", ".75em");

        d3.json(this.jsonDataURL, function(error, ret) {
            if (error) {console.log(ret.error);}
            //console.log(ret.data.cost_summary);
            var root = ret.data.cost_summary;
            _widgit.currency = ret.data.currency_base;
            _widgit.currency_year = ret.data.currency_year; 
            initialize(root);
            accumulate(root);
            layout(root);
            display(root);

            function initialize(root) {
                root.x = root.y = 0;
                root.dx = width;
                root.dy = height;
                root.depth = 0;
            }

            // Aggregate the values for internal nodes. This is normally done by the
            // treemap layout, but not here because of our custom implementation.
            // We also take a snapshot of the original children (_children) to avoid
            // the children being overwritten when when layout is computed.
            // TODO parseInt should really be parseFloat
            function accumulate(d) {
                return (d._children = d.children)
                    ? d.value = d.children.reduce(function(p, v) {
                        return parseInt(p) + accumulate(v); }, 0)
                    : d.value;
            }

            // Compute the treemap layout recursively such that each group of siblings
            // uses the same size (1×1) rather than the dimensions of the parent cell.
            // This optimizes the layout for the current zoom state. Note that a wrapper
            // object is created for the parent node for each group of siblings so that
            // the parent’s dimensions are not discarded as we recurse. Since each group
            // of sibling was laid out in 1×1, we must rescale to fit using absolute
            // coordinates. This lets us use a viewport to zoom.
            function layout(d) {
                if (d._children) {
                    treemap.nodes({_children: d._children});
                    d._children.forEach(function(c) {
                        c.x = d.x + c.x * d.dx;
                        c.y = d.y + c.y * d.dy;
                        c.dx *= d.dx;
                        c.dy *= d.dy;
                        c.parent = d;
                        layout(c);
                    });
                }
            }

            function display(d) {
                grandparent
                    .datum(d.parent)
                    .on("click", transition)
                    .select("text")
                    .text(name(d));

                var g1 = svg.insert("g", ".grandparent")
                    .datum(d)
                    .attr("class", "depth");

                var g = g1.selectAll("g")
                    .data(d._children)
                    .enter().append("g");

                g.filter(function(d) { return d._children; })
                    .classed("children", true)
                    .on("click", transition);


                g.append("rect")
                    .attr("class", "parent")
                    .call(rect)
                    .append("title")
                    .text(function(d) {
                        // append title text to the parent even though we'll never
                        // see this directly as a tooltip the text is used to 
                        // populate an info box outside the treemap
                        var cost = _widgit._format_currency(d);
                        return "Name: \"" + d.name + "\"\nCost: " + cost;
                        //return formatNumber(d.value);
                    });


                g.selectAll(".child")
                    .data(function(d) { return d._children || [d]; })
                    .enter().append("rect")
                    .attr("class", "child")
                    .call(rect)
                    .append("title")
                    .text(function(d) {
                        var cost = _widgit._format_currency(d);
                        return "Name: \"" + d.name + "\"\nCost: " + cost;
                        //return formatNumber(d.value);
                    });


                g.append("text")
                    .attr("dy", ".75em")
                    .text(function(d) { return d.name; })
                    .call(text);



                function transition(d) {

                    if (transitioning || !d) {
                        return;
                    }
                    else {
                        transitioning = true;
                    }

                    var g2 = display(d),
                        t1 = g1.transition().duration(750),
                        t2 = g2.transition().duration(750);

                    // Update the domain only after entering new elements.
                    x.domain([d.x, d.x + d.dx]);
                    y.domain([d.y, d.y + d.dy]);

                    // Enable anti-aliasing during the transition.
                    svg.style("shape-rendering", null);

                    // Draw child nodes on top of parent nodes.
                    svg.selectAll(".depth").sort(function(a, b) { return a.depth - b.depth; });

                    // Fade-in entering text.
                    g2.selectAll("text").style("fill-opacity", 0);

                    // Transition to the new view.
                    t1.selectAll("text").call(text).style("fill-opacity", 0);
                    t2.selectAll("text").call(text).style("fill-opacity", 1);

                    // check each text element and find the longest substring where the
                    // computed bounding box is smaller than the rect that the text will
                    // be placed into.  
                    t2.selectAll("text").call(text).each(function(d) {
                        var fudge_factor = 15;
                        var text_width = this.getBBox().width;
                        var rect_width = (x(d.x + d.dx) - x(d.x)) - fudge_factor;
                        if (text_width <= rect_width) {
                            return;
                        }
                        else {
                            for (var i = text_width-3; i > 0; i -= 3) {
                                if (this.getSubStringLength(0,i) <= rect_width) {
                                    this.textContent = d.name.substring(0, i) + "...";
                                    return;
                                }
                            }
                            this.textContent = "...";
                        }
                    });

                    t1.selectAll("rect").call(rect);
                    t2.selectAll("rect").call(rect);

                    // Remove the old node when the transition is finished.
                    t1.remove().each("end", function() {
                        svg.style("shape-rendering", "crispEdges");
                        transitioning = false;
                    });
                }

                return g;
            }

            function text(text) {
                text.attr("x", function(d) { return x(d.x) + 6; })
                    .attr("y", function(d) { return y(d.y) + 6; });
            }

            function rect(rect) {
                rect.attr("x", function(d) { return x(d.x); })
                    .attr("y", function(d) { return y(d.y); })
                    .attr("width", function(d) { return x(d.x + d.dx) - x(d.x); })
                    .attr("height", function(d) { return y(d.y + d.dy) - y(d.y); });

                if (rect.on && typeof(rect.on) == "function") {
                    if (rect.classed("child")) {
                        rect.on("mouseenter", function() {
                            var child_rect = $(this);
                            var parent_rect = $(child_rect.siblings()[0]);
                            _widgit.parent_title_div.text(parent_rect.text());
                            _widgit.child_title_div.text(child_rect.text());
                        });
                        rect.on("mouseleave", function() {
                            _widgit.parent_title_div.html("&nbsp");
                            _widgit.child_title_div.html("&nbsp");
                        });
                    }
                }
            }

            function name(d) {
                return d.parent
                    ? name(d.parent) + "." + d.name
                    : d.name;
            }
        }); // end of d3.json ajax call's scope //
      }
   });
})(jQuery);

