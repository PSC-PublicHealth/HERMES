/*
*/
;(function($){
	$.widget("vaccine-availability-by-cohort.vachart",{
		options:{
			jsonData:{},
			scrollable:false,
			resizable:false,
			width:255,
			height:300,
			title_font_size:12,
			legend_font_size:10,
			axis_font_size:9,
			axis_label_font_size:9,
			shrink_width:225,
			shrink_height:300,
			margin: [65,40,5,80],
			trant:{
				title:"Vaccine Availabity By Birth Cohort"
			}
		},
		
		_create:function(){
			trant = this.option.trant;

			this.containerID = $(this.element).attr('id');
			var containerID = this.containerID;
			var init_height = this.options.height;
			var init_width = this.options.width;
			var init_title_font = this.options.title_font_size;
			var init_legend_font = this.options.legend_font_size;
			var init_axis_font = this.options.axis_font_size;
			var init_axis_label_font = this.options.axis_label_font_size;
			var margin = this.options.margin;
			var chartData = this.options.jsonData;
			
			
			var phrases = {0:'Availability by Location',
			               1:'Birth Cohort Size',
			               2:'Availability',
			               3:'Number of Locations'};
			translate_phrases(phrases)
			.done(function(result){
				var tp = result.translated_phrases;
				var dats = []
				for(var i = 0; i < chartData.datas.length; i++){
					for(var j=0; j < chartData.categories.length; j++){
						dats.push({'Level':chartData.datas[i].name,
								  'Percentage':chartData.categories[j],
								  'Number of Locations':chartData.datas[i].data[j]
								  });
					}
				}
				
				console.log(dats);
				
				var svg= dimple.newSvg("#"+containerID,init_width,init_height);
				var myChart = new dimple.chart(svg,dats);
				var b = myChart.setBounds(margin[0],margin[1],
										  init_width-margin[0]-margin[2],
										  init_height-margin[1]-margin[3]-40);
				
				x = myChart.addMeasureAxis("x","Number of Locations");
				myChart.defaultColors = [
				                      new dimple.color("#4573A7"),
				                      new dimple.color("#71588F"),
				                      new dimple.color("#AA4644"),
				                      new dimple.color("#4298AF"),
				                      new dimple.color("#DB843D"),
				                      new dimple.color("#93A9D0"),
				                      new dimple.color("#D09392"),
				                      new dimple.color("#BACD96"),
				                      new dimple.color("#A99BBE")
				                      ];
				x.ticks = 3;
				y = myChart.addCategoryAxis("y",['Percentage',"Level"]);
				y.addOrderRule(chartData.categories,true);
				var ser = myChart.addSeries("Level",dimple.plot.bar);
				ser.barGap = 0;
				var legend = myChart.addLegend(60,init_height-margin[3]+20,init_width-10,40,"left");
				//ser.stacked = false;
				myChart.draw();
				
				x.titleShape.text(tp[3])
				y.titleShape.text(tp[2]);
				
				
				svg.append("text")
				.attr("x",myChart._xPixels() + myChart._widthPixels()/2)
				.attr("y",myChart._yPixels() -20)
				.style("text-anchor","middle")
				.style("font-size","12px")
				.text(tp[0]);
							
				svg.append("text")
					.attr("x",legend._xPixels()+10)
					.attr("y",legend._yPixels()-10)
					.style("text-anchor","middle")
					.style("font-size","10px")
					.style("font-weight","bold")
					.text(tp[1])
			});
		}
	});
})(jQuery);
