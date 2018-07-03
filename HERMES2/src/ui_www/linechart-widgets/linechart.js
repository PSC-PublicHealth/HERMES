/*
*/

;(function($){
    $.widget("linecharts.vialsplot",{
        options:{
            scrollable:false,
            resizable:false,
            modelId:-1,
            resultsId:-1,
            storeId:-1,
            vials:true,
            width:600,
            height:200,
            hideAllButTotal:true,
            rootPath:'',
            trant:{
        		title:"Vials Plot Chart"
    		}
    	},	
 
	    _create:function(){
			trant = this.option.trant;
		
			this.containerID = $(this.element).attr('id');
			var containerID = this.containerID;
			$("#"+this.containerID).css('width',"600px");
			$("#"+this.containerID).css('height',"200px");
			$("#"+this.containerID).css('margin-top',"30px");
			
			var chartID = this.containerID + "_chart";
			var y_axisID = this.containerID + "_y_axis";
			var x_axisID = this.containerID + "_x_axis";
			var x_labelID = this.containerID + "_x_label";
			var y_labelID = this.containerID + "_y_label";
			var legendID = this.containerID + "_legend";
			
			var url = this.options.vials ? this.options.rootPath + 'json/get-vials-plot-for-store' : this.options.rootPath + 'json/get-fill-ratio-time-for-store';
			var ylabel = this.options.vials ? 'Vials' : '% Filled';
			
			
			$("#"+this.containerID).append("<div class='linechartWidget_y_axis' id='" + y_axisID + "'"+
				" style='position:absolute;z-index:10;top:0;bottom:0;left:20px;width:60px;'></div>");
			
			$("#"+this.containerID).append("<div class='linechartWidget_ylabel' id='"+ y_labelID + "'"+
				"style='position:absolute;left:0px;top:80px;-ms-transform:rotate(270deg);-moz-transform:rotate(270deg);-webkit-transform:rotate(270deg);-o-transform:rotate(270deg);'></div>");
			
			$("#"+this.containerID).append("<div class='linechartWidget_chart' id='" + chartID + "'"+
				" style='position:relative;left:80px;'></div>");
			
			$("#"+this.containerID).append("<div class='linechartWidget_x_axis' id='" + x_axisID + "'"+
				"style='position:absolute;left:80px;height:80px;'></div>");
			
			$("#"+this.containerID).append("<div class='linechartWidget_xlabel' id='"+ x_labelID + "'"+
				"style='position:absolute;left:220px;bottom:10px;'></div>");
			$("#"+this.containerID).append("<div class='linechartWidget_legend' id='" + legendID + "'"+
				"style='position:absolute;top:10px;left:600px;color:black;background-color:white; display:inline-block;"+
				"vertical-align:top;margin:0 0 0 10px;'></div>");
				
			this.svgContainerID = this.containerID+"svgContainer";
			var svgContainerID = this.svgContainerID;
			
			var modelId = this.options.modelId;
			var resultsId = this.options.resultsId;
			var storeId = this.options.storeId;
			var rootPath = this.options.rootPath;
			var vials = this.options.vials;
			
			
				
			var phrases = { 0:'Days',
			                1:ylabel
						  };
			
			var colors = ['blue','red','green','orange','purple','yellow','black','brown']		 
			translate_phrases(phrases)
				.done(function(tphrases){
					var tp = tphrases.translated_phrases;
					
					$.ajax({
						url:url,
						datatype:'json',
						data:{'modelId':modelId,
							  'resultsId':resultsId,
							  'storeId':storeId
							}
					})
					.done(function(result){
						if(!result.success){
							alert(result.msg);
						}
						else{
							var palette = new Rickshaw.Color.Palette ({ scheme: 'colorwheel' });
							var seriesData = [];
							for(var i = 0; i<result.dataList.length;i++){
								seriesData.push({'name':result.dataList[i].name,
												 'color':palette.color(),
												 'data':result.dataList[i].data});
							}
							
							
							$("#"+x_labelID).html("<p style='font-size:14px;'>"+tp[0]+"</p>");
							$("#"+y_labelID).html("<p style='font-size:14px;'>"+tp[1]+"</p>");
							
							
							var graph = new Rickshaw.Graph({
								element: document.getElementById(chartID),
								renderer:'line',
								interpolation:'step-after',
								stroke:true,
								preserve: true,
								width:500,
								height:150,
								min:0,
								series: seriesData
							});
							
							
							if(!vials){
								graph.configure({max:100});
							}
							
							var xaxes = new Rickshaw.Graph.Axis.X({
								element:document.getElementById(x_axisID),
								graph: graph,
								orientation:'bottom'
							});
							
							var yaxis;
							if(vials){
								yaxis = new Rickshaw.Graph.Axis.Y({
									element:document.getElementById(y_axisID),
									graph:graph,
									orientation:'left',
									tickFormat: function(y){return y;}
										
								});
							}
							else{
								yaxis = new Rickshaw.Graph.Axis.Y({
									element:document.getElementById(y_axisID),
									graph:graph,
									orientation:'left',
									tickFormat: function(y){return y + "%";}
								});
							}
							
							graph.render();
							
							var legend = new Rickshaw.Graph.Legend({
								element: document.getElementById(legendID),
								graph:graph
							});
							
							var shelving = new Rickshaw.Graph.Behavior.Series.Toggle({
								graph: graph,
								legend:legend
							});
							
							var order = new Rickshaw.Graph.Behavior.Series.Order( {
								graph: graph,
								legend: legend
							} );
							var highlighter = new Rickshaw.Graph.Behavior.Series.Highlight( {
								graph: graph,
								legend: legend
							});
							
							var hoverDetail = new Rickshaw.Graph.HoverDetail({
								graph:graph,
								formatter: function(series, x, y){
									var content = series.name + " <br>Day: " + x + "<br>Vials: " +y;
									return  content;
								}
							
							});
							
							//setting Css here, cause I have no fucking idea how else to do it.
							$("#"+legendID+" .action").css('opacity',1.0);
							$('#'+y_axisID +' svg').css('height',parseFloat($('#'+y_axisID + ' svg').attr("height"))+10 + "px")
							var hideallbutTotsl = $("#"+legendID+" .label")[0].click();

						}
					});
				});
			
		}

    });   
})(jQuery);
   
