;(function($){
	function moneyFormatter(cellValue, options, rowObject) {
		if (cellValue) {
			if (cellValue.formatMoney)
				return cellValue.formatMoney();
			else
				return cellValue			
		}
		else
			return (0.0).formatMoney()
	}
	$.widget("results_widgets.csgrid",{
		options:{
			resultsId:-1,
			modelId:-1,
			scrollable:false,
			resizable:true,
			trant:{
				title:"Cost Summary Grid"
			}
		},
		
		hideMinor:function(){
			this.containerID = $(this.element).attr('id');
			console.log("Cont: "+this.containerID);
			//$("#"+this.containerID).jqGrid('hideCol',["percooler",'perfreezer','dosespervial']);
		},
		showMinor:function(){
			this.containerID = $(this.element).attr('id');
			console.log("Cont: "+this.containerID);
			//$("#"+this.containerID).jqGrid('showCol',["percooler",'perfreezer','dosespervial']);
		},
		_create:function(){
			trant = this.option.trant;

			this.containerID = $(this.element).attr('id');
			var containerID = this.containerID;
			
			var resultsId = this.options.resultsId;
			var modelId = this.options.modelId;
			
			var chartData = this.options.jsonData;
			
			$.getJSON('json/costs-summary-layout',
				{
					modelId:modelId,
					resultsId:resultsId
				})
			.done(function(data) {
				if (data.success) {
					if (data.columns.length>0) {
						var colNameList = [data.levelTitle];
						var colModelList = [
								 	          {
								 	        	  name:'ReportingBranch',
								 	        	  index:'ReportingBranch',
								 	        	  jsonmap:'ReportingBranch',
								 	        	  hidden:false, 
								 	        	  key:true,
								 	        	  sortable:false
								 	          },
						                    ];
						for (var i = 0; i<data.columns.length; i++) {
							colNameList.push(data.colHeadings[i]);
							colModelList.push(
						 	          {
						 	        	  name:data.columns[i],
						 	        	  index:data.columns[i],
						 	        	  jsonmap:data.columns[i],
						 	        	  hidden:false, 
						 	        	  formatter:moneyFormatter,
						 	        	  sortable:false
						 	          }
									);
						}
						$("#"+containerID).jqGrid({ //set your grid id
					 		url:'json/costs-summary?modelId='+modelId+'&resultsId='+resultsId,
						 	datatype: "json",
						 	jsonReader: {
						 		root:'rows',
						 		repeatitems: false,
						 		id:'ReportingBranch'
						 	},
						 	sortable:true,
						 	caption:data.title,
						 	width: 'auto', //specify width; optional
						 	height:'auto',
						 	autowidth:'true',
						 	colNames:colNameList,
						 	colModel:colModelList,
						 	gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
						    footerrow: true,
						    gridComplete: function() {
						        var $grid = $("#"+containerID);
						        var vals = {ReportingBranch:data.totalLabel};
						        for (var i = 0; i<data.columns.length; i++) {
						        	var colEntries = $grid.jqGrid('getCol', data.columns[i], false);
						        	var colSum = 0.0
						        	for (var j = 0; j<colEntries.length; j++) colSum += colEntries[j].unformatMoney();
						        	vals[data.columns[i]] = colSum.formatMoney();
						        }
					        	$grid.jqGrid('footerData', 'set', vals);
						    }
						}).jqGrid('hermify',{debug:true, resizable_hz:true});						
					}
					else {
						$("#"+containerID).html(data.title);
					}
				}
				else {
					alert('{{_("Failed: ")}}'+data.msg);
				}
			})
		.fail(function(jqxhr, textStatus, error) {
				alert('{{_("Error: ")}}'+jqxhr.responseText);
			});
		}
	});
})(jQuery);
	

			
			