/*
###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
# =============================================================================== #
#                                                                                 #
# Permission to use, copy, and modify this software and its documentation without # 
# fee for personal use within your organization is hereby granted, provided that  #
# the above copyright notice is preserved in all copies and that the copyright    # 
# and this permission notice appear in supporting documentation.  All other       #
# restrictions and obligations are defined in the GNU Affero General Public       #
# License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
# copy of the license is also provided in the top level of the source directory,  #
# in the file LICENSE.txt.                                                        #
#                                                                                 #
###################################################################################
*/
;(function($){
	$.widget("storage-utilization-by-level.suchart",{
		options:{
			jsonData:{},
			scrollable:false,
			resizable:false,
			width:300,
			height:400,
			title_font_size:12,
			legend_font_size:10,
			axis_font_size:9,
			axis_label_font_size:9,
			shrink_width:225,
			shrink_height:300,
			trant:{
				title:"Storage Utilization By Level"
			}
		},
		shrink:function(){
			$("#"+this.containerID).highcharts().setSize(this.options.shrink_width,
														this.options.shrink_height,
														false);
		},
		grow:function(){
			$("#"+this.containerID).highcharts().setSize(this.options.width,this.options.height,false);
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
			
			var chartData = this.options.jsonData;
			
			var phrases = {0:"Maximum Storage Utilization by Location",
			               1:"Levels",
			               2:"Utilization",
			               3:"Number of Locations"};
			
			translate_phrases(phrases)
			.done(function(result){
				console.log("Storage");
				console.log(result);
				console.log(chartData);
				var tp = result.translated_phrases;
				$("#"+containerID).highcharts({
					chart : {
					type : 'bar',
					height : init_height,
					width : init_width
				},
				title : {
					style:{
						fontSize: init_title_font + 'px'
					},
					text : tp[0]
				},
				legend : {
					enabled : true,
					align:'center',
					itemStyle:{
						fontSize: init_legend_font + 'px'
					},
					title: {
						style:{
							fontSize:init_legend_font + 'px'
						},
						text: tp[1]
					}
				},
				xAxis : {
					labels:{
						style:{
							fontSize: init_axis_font + 'px'
						}
					},
					categories : chartData.categories,
					title : {
						style:{
							fontSize: init_axis_label_font + 'px'
						},
						text : tp[2]
					}
				},
				yAxis : {
					min : 0,
					labels:{
						style:{
							fontSize: init_axis_font + 'px'
						}
					},
					title : {
						style:{
							fontSize: init_axis_label_font + 'px'
						},
						text : tp[3]
					}
				},
				plotOptions : {
					bar: {
						dataLabels : {
							enabled : false
						},
		            	groupPadding: 0,
		            	pointPadding: 0,
		            	borderWidth: 0
					}
				},
				credits : {
					enabled : false
				},
				series : chartData.datas
				});
			}); 
		}
	});
})(jQuery);
	
		