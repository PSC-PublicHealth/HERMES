/*
*/


;(function($){
	var myChart;
	var x,y;
	var xlab,ylab;
    $.widget("barcharts.vabarchart",{
        options:{
            scrollable:false,
            resizable:false,
            modelId:-1,
            resultsId:-1,
            storeId:-1,
            width:800,
            height:200,
            margin: [30, 70, 200, 100], 
            hideAllButTotal:true,
            rootPath:'',
            trant:{
        		title:"VA Bar Chart"
    		}
    	},	
 
    	redraw: function(){
    		myChart.draw();
    		x.titleShape.style("font-size","12px").text(xlab);
			y.titleShape.style("font-size","12px").text(ylab);
    		
    	},

    	_create: function(){
    		trant = this.option.trant;
	
			this.containerID = $(this.element).attr('id');
			var containerID = this.containerID;
			//$("#"+this.containerID).css('width',this.options.width);
			//$("#"+this.containerID).css('height',this.options.height);
			
			$("#"+this.containerID).append("<div class='barChartWidget_ylabel' id='"+ y_labelID + "'"+
				"style='position:absolute;left:0px;top:80px;-ms-transform:rotate(270deg);-moz-transform:rotate(270deg);-webkit-transform:rotate(270deg);-o-transform:rotate(270deg);'></div>");
			
			var modelId = this.options.modelId;
			var resultsId = this.options.resultsId;
			var storeId = this.options.storeId;
			var rootPath = this.options.rootPath;
			var width = this.options.width;
			var height = this.options.height;
			var y_labelID = this.containerID + "_y_label";
			
			var margin = {'top':this.options.margin[0],
			              'bottom':this.options.margin[1], 
			              'left':this.options.margin[2],
			              'right':this.options.margin[3]};
			
			console.log(margin);
			
			var phrases = {0:'percent available',
			               1:'vaccines',
			               2:'Availability by Vaccine',
			               3:'Availability',
			               4:'Vaccine'}
			
			translate_phrases(phrases)
				.done(function(tphrases){
					var tp = tphrases.translated_phrases;
					xlab = tp[0];
					ylab = tp[1];
					$.ajax({
						url:rootPath+'json/get-vaccine-availability-plot-for-store',
						dataytpe:'json',
						data:{
							'modelId':modelId,
							'resultsId':resultsId,
							'storeId':storeId
						}
					})
					.done(function(result){
						if(!result.success){
							alert(result.msg);
						}
						else{
							var svg = dimple.newSvg("#"+containerID,width,height);
							myChart = new dimple.chart(svg,result.dataList);
							var b = myChart.setBounds(
									                  margin.left,
									                  margin.top,
									                  width - margin.right - margin.left,
									                  height - margin.bottom
													  );
							
							x = myChart.addMeasureAxis("x","value");
							x.overrideMin = 0.0;
							x.overrideMax = 1.0;
							x.ticks = 5;
							x.tickFormat = "%";
							
							y = myChart.addCategoryAxis('y','label');
							y.addOrderRule(result.data.categories,true);
							var ser = myChart.addSeries(null,dimple.plot.bar);
							ser.barGap = 0.5;
							ser.getTooltipText = function (e){
								return [tp[4] + ": " + e.y,
								        tp[3] + ': '+ (parseFloat(e.xValue)*100.00).toFixed(2) + "%"];
							};
							myChart.draw();
							x.titleShape.style("font-size","12px").text(tp[0]);
							y.titleShape.style("font-size","12px").text(tp[1]);
							
							
							svg.append("text")
								.attr("x",myChart._xPixels() + myChart._widthPixels()/2)
								.attr("y",myChart._yPixels() -10)
								.style("text-anchor","middle")
								.style("font-size","18px")
								.text(tp[2]);
							
							ser.shapes.each(function(d){
								var shape = d3.select(this);
								if(d.y == "All Vaccines") shape.style("fill","red");
								sheight = myChart.y + myChart.height - y._scale(d.height);
								swidth = x._scale(d.width);
								svg.append("text")
									.attr("x",parseFloat(shape.attr("x")) + width - margin.left-30)
									.attr("y",parseFloat(shape.attr("y")) + parseFloat(shape.attr("height")/2+3.5))
									.style("text-anchor","end")
									.style("font-size","10px")
									.text(function(){
										if(d.xValue == 1.0){
											return "100.00%";
										}
										else{
											return (parseFloat(d.xValue)*100.00).toFixed(2) + "%";
										}
									});
							});
							
							$("#"+y_labelID).html("<p style='font-size:14px;'>"+tp[1]+"</p>");
						}
					});
				});	
    	}
    });
    
})(jQuery);


    	
