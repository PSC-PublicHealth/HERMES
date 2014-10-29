;(function($) {
    $.widget("hierarchical.treemap", {
        options: {
            file: "static/hierarchical-charts/readme.json",
            //jsonDataURLBase: "json/results-cost-hierarchical",
            //jsonDataURLParameters: ["modelId=3", "resultsId=6"],
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


        _create: function() {
    
            trant = this.options.trant;

            this.containerID = $(this.element).attr('id');
            $(this.element).css({
                float: "left"
            });
            this.svgContainerID = this.containerID+"svgContainer";
            d3.select("#"+this.containerID).append("svgContainer")
                .attr("id", this.svgContainerID);
   
            var jsonDataURL = this.options.jsonDataURLBase + "?"
                            + this.options.jsonDataURLParameters.join("&");
    
            $("<link/>", {
               rel: "stylesheet",
               type: "text/css",
               href: "static/hierarchical-charts/zoomable-treemap.css"
            }).appendTo("head");
   










        }
    });
})(jQuery);

