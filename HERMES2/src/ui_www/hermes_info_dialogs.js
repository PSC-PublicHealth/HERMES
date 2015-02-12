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
// Dialog box functions

function open_store_info_box(rootPath,modelId,storeId,storeName,resultId){
	iShowRes = 0;
	if(resultId > 0) iShowRes = 1;

	var divIDName = "storeInfo_" + Math.random().toString(36).replace(/[^a-z]+/g,'');
	$.ajax({
		url: rootPath+'json/dialoghtmlforstore',
		dataType:'json',
		data:{name:divIDName,geninfo:1,utilinfo:iShowRes,popinfo:1,storedev:1,transdev:1,
			  vacavail:iShowRes,fillratio:iShowRes,invent:iShowRes,availplot:iShowRes}
	})
	.done(function(result){
		if(!result.success){
			alert(result.msg);
		}
		else{
			$(document.body).append(result.htmlString);
			var meta_data = eval(divIDName + "_meta");
			populateStoreInfoDialog(rootPath,divIDName,meta_data,modelId,storeId,resultId);
			$("#"+divIDName+"_dialog").dialog("option","title","Information for Location "+ storeName + "("+ storeId+")");
			$("#"+divIDName+"_dialog").dialog("open");
		}
	});
}

function open_route_info_box(rootPath,modelId,routeId,resultId){
	iShowRes = 0;
	if(resultId > 0) iShowRes = 1;
	
	var divIDName = 'route_info_' + Math.random().toString(36).replace(/[^a-z]+/g,'');
	$.ajax({
		url: rootPath+'json/dialoghtmlforroute',
		dataType:'json',
		data:{name:divIDName,geninfo:1,utilinfo:iShowRes,tripman:iShowRes},
		success:function(result){
			if(!result.success){
				alert(result.msg);
			}
			else{
				$(document.body).append(result.htmlString);
				var meta_data = eval(divIDName + '_meta');
				populateRouteInfoDialog(rootPath,divIDName,meta_data,modelId,routeId,resultId);
				$("#"+divIDName+"_dialog").dialog("option","title","Information for Route "+ routeId);
				$("#"+divIDName+"_dialog").dialog("open");
			}
		}	
	});
};
	
function populateStoreInfoDialog(rootPath,divName,meta,modId,storId,resId){
	//console.log("creating for div "+divName+ " modelID = " + modId + " storeID = " + storId);
	$("#" + divName+"_content").tabs();
	if (meta['genInfo']){
		console.log("#"+divName+"_GenInfo");
		$("#"+divName+"_GenInfo").jqGrid({
			url:rootPath + 'json/get-general-info-for-store',
				//&modelId='+modId+'&storeId='+storId,
			datatype: 'json',
			postData:{modelId:modId,storeId:storId},
			jsonReader: {
				repeatitems: false,
				id:"id",
				root:"rows"
			},
			sortable:false,
			captions:'General Info',
			width: 'auto',
			height:'auto',
			colNames: ['Feature','Value'],
			colModel : [{
				name : 'feature',
				index : 'feature',
				width : 100,
				sortable : false
			}, {
				name : 'value',
				id : 'value',
				width : 200,
				sortable : false
			}],
		});
		$("#"+divName+"_GenInfo").parents("div.ui-jqgrid-view").children("div.ui-jqgrid-hdiv").hide();
		
	}
	
	if (meta['utilInfo']){
		var phrases = {0:'Information',1:'Placemark',2:'Category',3:'Data',4:'Utilization Statistics'};
		//var phrase = {'Name','Count','2-8C Net Storage','Below 2C Net Storage'};
		$.ajax({
			url:'json/translate',
			dataType:'json',
			data:phrases,
			type:"post",
			async:false,
			success:function(data){
					$("#"+divName+"_Utilization").jqGrid({
						url:rootPath + 'json/get-storage-utilization-for-store',
						datatype: 'json',
						postData:{modelId:modId,storeId:storId,resultsId:resId},
						jsonReader: {
							repeatitems: false,
							root:"rows"
						},
						height : 'auto',
						width : 500,
						scroll : false,
						scrollOffset : 0,
						colNames : data.translated_phrases.slice(0,4),
						colModel : [{
							name : 'info',
							id : 'info',
							sortable : false,
							hidden : true,
							width : 0
						}, {
							name : 'placemark',
							id : 'placemark',
							width : 50
						}, {
							name : 'category',
							id : 'category',
							sortable : false
						}, {
							name : 'value',
							id : 'value',
							sortable : false,
							align : 'right',
							formatter : "number",
							formatoptions : {
								decimalPlaces : 2
							}
						}],
						grouping : true,
						groupingView : {
							groupField : ['info'],
							groupColumnShow : false,
							groupOrder : ['desc'],
						},
						caption : data.translated_phrases[4]
					});
					$("#"+divName+"_Utilization").parents("div.ui-jqgrid-view").children("div.ui-jqgrid-hdiv").hide();
			}
		});
		
		
	}
	
	if (meta['popInfo']){
		var phrases = {0:'Category',1:'Count',2:'Population Information'};
		$.ajax({
			url:'json/translate',
			dataType:'json',
			data:phrases,
			type:"post",
			async:false,
			success:function(data){
				$("#"+divName+"_PopInfo").jqGrid({
					url:rootPath + 'json/get-population-listing-for-store',
					postData:{modelId:modId,storeId:storId},
					datatype:'json',
					jsonReader: {
						repeatitems: false,
						id:"id",
						root:"rows"
					},
					height : 'auto',
					width : 300,
					scroll : false,
					scrollOffset : 0,
					colNames : data.translated_phrases.slice(0,2),
					colModel : [{
						name : 'class',
						index: 'class',
						width : 200
					}, {
						name : 'count',
						index : 'count',
						align : 'right',
						sortable: false
							
					}],
					caption : data.translated_phrases[3]
				});
			}
		});
	}
	
	if(meta['storeDev']){
		var phrases = {0:'Name',1:'Count',2:'2-8C Net Storage',3:'Below 2C Net Storage',4:'Storage Devices'};
		//var phrase = {'Name','Count','2-8C Net Storage','Below 2C Net Storage'};
		$.ajax({
			url:'json/translate',
			dataType:'json',
			data:phrases,
			type:"post",
			async:false,
			success:function(data){
				console.log(data);
				$("#"+divName+"_StoreDevInfo").jqGrid({
					url:rootPath + 'json/get-device-listing-for-store',
					postData:{modelId:modId,storeId:storId},
					datatype:'json',
					jsonReader: {
						repeatitems: false,
						id:"id",
						root:"rows"
					},
					height : 'auto',
					width : 600,
					scroll : false,
					scrollOffset : 0,
					colNames : data.translated_phrases.slice(0,4),
					colModel : [{
						name : 'name',
						index: 'name',
						width : 300
					}, {
						name : 'count',
						index : 'count',
						align : 'right',
						width : 60,
						sortable : false
					}, {
						name : 'cooler',
						index : 'cooler',
						align : 'right',
						formatter : "number",
						formatoptions : {
							decimalPlaces : 2
						}
					}, {
						name : 'freezer',
						id : 'freezer',
						align : 'right',
						formatter : "number",
						formatoptions : {
							decimalPlaces : 2
						}
					}],
					caption : data.translated_phrases[4]
				});
			}
		});
	}
	
	if(meta['transDev']){
		var phrases = {0:'Name',1:'Count',2:'2-8C Net Storage (L)',3:'Below 2C Net Storage (L)',4:'Vehicle Information'};
		//var phrase = {'Name','Count','2-8C Net Storage','Below 2C Net Storage'};
		$.ajax({
			url:'json/translate',
			dataType:'json',
			data:phrases,
			type:"post",
			async:false,
			success:function(data){
				$("#"+divName+"_TransDevInfo").jqGrid({
					url:rootPath + 'json/get-transport-listing-for-store',
					postData:{modelId:modId,storeId:storId},
					datatype:'json',
					jsonReader: {
						repeatitems: false,
						id:"id",
						root:"rows"
					},
					height : 'auto',
					width : 'auto',
					scroll : false,
					scrollOffset : 0,
					colNames : data.translated_phrases.slice(0,4),
					colModel : [{
						name : 'name',
						id : 'name',
						width : 300
					}, {
						name : 'count',
						id : 'count',
						align : 'right',
						width : 60,
						sortable : false
					}, {
						name : 'fridge',
						id : 'fridge',
						jsonmap:'cooler',
						align : 'right',
						formatter : "number",
						formatoptions : {
							decimalPlaces : 2
						}
					}, {
						name : 'freezer',
						id : 'freezer',
						jsonmap:'freezer',
						align : 'right',
						formatter : "number",
						formatoptions : {
							decimalPlaces : 2
						}
					}],
					caption : data.translated_phrases[4]
				});
			}
		});
	}

	if(meta['vaccAvail']){
		var phrases = {0:'Vaccine',1:'Doses Demanded',2:'Doses Administered',3:'Vials Administered',
						4:'Stockout Days',5:'Vials Expired',6:'Availability',7:'Vaccine Statistics'};
		$.ajax({
			url:'json/translate',
			dataType:'json',
			data:phrases,
			type:"post",
			async:false,
			success:function(data){
				$.ajax({
					url:rootPath + 'json/get-vaccine-stats-for-store',
					datatype:'json',
					data:{'modelId':modId,
						  'storeId':storId,
						  'resultsId':resId},
					method:'post'
				})
				.done(function(result){
					if(!result.success){
						alert(result.msg);
					}
					else{
						if(result.rows[0].name == "All Vaccines" && result.rows[0].patients == 0){
							$("[aria-controls='tab-8']").remove();
							$("[aria-controls='tab-9']").remove();
						}
						else{
							$("#"+divName+"_Availability").jqGrid({
								//url:rootPath + 'json/get-vaccine-stats-for-store',
								//postData:{modelId:modId,storeId:storId,resultsId:resId},
								datastr:result,
								datatype:'jsonstring',
								jsonReader: {
									repeatitems: false,
									root: 'rows',
									page: function(obj){console.log("OBJ = " + obj); return 1;}
								},
								height : 'auto',
								width : 'auto',
								scroll : false,
								scrollOffset : 0,
								colNames : data.translated_phrases.slice(0,7),
								colModel : [{
									name : 'name',
									id : 'name',
									jsonmap: 'name',
									width: 300,
								}, {
									name : 'patients',
									id : 'patients',
									jsonmap:'patients',
									align : 'right',
									width : 100
								}, {
									name : 'treated',
									id : 'treated',
									jsonmap:'treated',
									align : 'right',
									width : 100
								}, {
									name : 'vials',
									id : 'vials',
									jsonmap:'vials',
									align : 'right',
									width : 100
								}, {
									name : 'outages',
									id : 'outages',
									jsonmap:'outages',
									align : 'right',
									width : 75
								}, {
									name: 'expired',
									id : 'expired',
									jsonmap:'expired',
									align : 'right',
									width : 75
								}, {
									name : 'avail',
									id : 'avail',
									jsonmap:'avail',
									align : 'right',
									formatter : "number",
									formatoptions : {
										decimalPlaces : 2
									}
								}],
								caption : data.translated_phrases[7]
							});
							if(meta['availPlot']){
								$("#"+divName+"_AvailPlot").vabarchart({
									modelId:modId,
									resultsId:resId,
									storeId:storId,
									rootPath:rootPath
								});
							}
						}
					}
				});
			}
		});
	}
	
	if(meta['invent']){
		$("#"+divName+"_VialsPlot").vialsplot({
			modelId:modId,
			resultsId:resId,
			storeId:storId,
			rootPath:rootPath
		});
	}
	
	if(meta['fillRatio']){
		$("#"+divName+"_FillPlot").vialsplot({
			modelId:modId,
			resultsId:resId,
			storeId:storId,
			rootPath:rootPath,
			vials:false
		});
	}
	
}

function populateRouteInfoDialog(rootPath,divName,meta,modId,rouId,resId){
	$("#" + divName+"_content").tabs();
	if (meta['genInfo']){
		var phrases = {0:'Feature',1:'Value',2:'Route Information'}
		$.ajax({
			url:'json/translate',
			dataType:'json',
			data:phrases,
			type:"post",
			async:false,
			success:function(data){
					$("#"+divName+"_RGenInfo").jqGrid({
						url:rootPath+'json/get-general-info-for-route',
						postData:{modelId:modId,routeId:rouId},
						datatype :'json',
						jsonReader: {
							repeatitems: false,
							root: 'rows',
							page: 1
						},
						ajaxGridOptions: {
						      type    : 'post',
						      error   : function() { alert('Something bad happened. Stopping');},
						},
						height : 'auto',
						width : 550,
						scroll : false,
						scollOffset : 0,
						colNames : data.translated_phrases.slice(0,2),
						colModel : [{
							name : 'feature',
							id : 'feature',
							width : '30%',
							sortable : false
						}, {
							name : 'value',
							id : 'value',
							width : '70%',
							sortable : false
						}],
						//caption : data.translated_phrases[2]
					}); 
					$("#"+divName+"_RGenInfo").parents("div.ui-jqgrid-view").children("div.ui-jqgrid-hdiv").hide();
				}
			});
		
	}
	
	if (meta['utilInfo']){
		var phrases = {0:'Feature',1:'Value',2:'Route Information'}
		$.ajax({
			url:'json/translate',
			dataType:'json',
			data:phrases,
			type:"post",
			async:false,
			success:function(data){
					$("#"+divName+"_RUtilInfo").jqGrid({
						url:rootPath+'json/get-utilization-for-route',
						postData:{modelId:modId,routeId:rouId,resultsId:resId},
						datatype :'json',
						jsonReader: {
							repeatitems: false,
							root: 'rows',
							page: 1
						},
						ajaxGridOptions: {
						      type    : 'post',
						      error   : function() { alert('Something bad happened. Stopping');},
						},
						height : 'auto',
						width : 550,
						scroll : false,
						scollOffset : 0,
						colNames : data.translated_phrases.slice(0,2),
						colModel : [{
							name : 'feature',
							id : 'feature',
							width : '30%',
							sortable : false
						}, {
							name : 'value',
							id : 'value',
							width : '70%',
							sortable : false
						}],
						//caption : data.translated_phrases[2]
					}); 
					$("#"+divName+"_RUtilInfo").parents("div.ui-jqgrid-view").children("div.ui-jqgrid-hdiv").hide();
				}
			});
	}
	
	if (meta['tripMan']){
		var phrases = {0:'Origin',1:'Destination',2:'Start',3:'End',4:'Volume Carried (L)',5:'Trips'};
		$.ajax({
			url:'json/translate',
			dataType:'json',
			data:phrases,
			type:"post",
			async:false,
			success:function(data){
				$("#"+divName+"_RTripMan").jqGrid({
					url:rootPath+'json/get-tripman-for-route',
					postData:{modelId:modId,routeId:rouId,resultsId:resId},
					datatype :'json',
					jsonReader: {
						repeatitems: false,
						root: 'rows',
						page: 1
					},
					ajaxGridOptions: {
					      type    : 'post',
					      error   : function() { alert('Something bad happened. Stopping');},
					},
					height : 'auto',
					width : 600,
					scroll : false,
					scollOffset : 0,
					colNames : data.translated_phrases.slice(0,5),
					colModel : [{
						name : 'origin',
						id : 'origin',
						jsonmap:'start',
						width : 200,
						sortable : false
					}, 
					{
						name : 'dest',
						id : 'dest',
						jsonmap:'end',
						width : 200,
						sortable : false
					}, {
						name : 'start',
						id : 'start',
						jsonmap:'tStart',
						width : 100,
						sortable : false,
						formatter : "number",
						formatoptions : {
							decimalPlaces : 2
						}
					}, {
						name : 'end',
						id : 'end',
						jsonmap:'tEnd',
						width : 100,
						sortable : false,
						formatter : "number",
						formatoptions : {
							decimalPlaces : 2
						}
					}, {
						name : 'vol',
						id : 'vol',
						jsonmap:'LitersCarried',
						sortable : false,
						formatter : "number",
						formatoptions : {
							decimalPlaces : 0
						}
					}],
					caption : data.translated_phrases[5]
				});
			}
		});
	}
}



function createVialsPlot(divName,rootPath,modId,storId,resId) {
	$("#"+divName).vialsplot({
		modelId:modId,
		resultsId:resId,
		storId:storId,
		rootPath:rootPath
		});
/*
	var phrases = {0:'Days',1:'Vials'}
	$.ajax({
		url:'json/translate',
		dataType:'json',
		data:phrases,
		type:"post",
		async:false,
		success:function(data){
			$('#' + divName).highcharts({
				chart : {
					//type : 'line',
					height : 300,
					width : 800
				},
				title : {
					text : null
				},
				legend : {
					enabled : true,
					itemWidth:100,
					align: "right",
					float: false,
					width:130,
					reversed: true
					
				},
				plotOptions : {
					series : {
						marker : {
							enabled : false
						}
					}
				},
				xAxis : {
					title : {
						text : data.translated_phrases[0]
					}
				},
				yAxis : {
					title : {
						text : data.translated_phrases[1]
					},
					min : 0,
					endOnTick : false
				},
				credits : {
					enabled : false
				},
				series : plotData
			});
			for (var i=0;i< $("#"+divName).highcharts().series.length;i++){
				if ($("#"+divName).highcharts().series[i].name != "All Vaccines"){
					$("#"+divName).highcharts().series[i].hide();
				}
			}
		}
	});
	*/
};

function createFillRatioPlot(divName, plotData) {
	var phrases = {0:'Days',1:'% Filled'}
	$.ajax({
		url:'json/translate',
		dataType:'json',
		data:phrases,
		type:"post",
		async:false,
		success:function(data){
			$('#' + divName).highcharts({
				chart : {
					type : 'spline',
					height : 300,
					width : 800
				},
				title : {
					text : null
				},
				legend : {
					enabled : true,
					itemWidth:100,
					align: "right",
					float: false,
					width:130,
					reversed: true
					
				},
				plotOptions : {
					series : {
						marker : {
							enabled : false
						}
					}
				},
				xAxis : {
					title : {
						text : data.translated_phrases[0]
					}
				},
				yAxis : {
					title : {
						text : data.translated_phrases[1]	
					},
					min : 0,
					max : 100,
					endOnTick : false
				},
				credits : {
					enabled : false
				},
				series : plotData
			});
		}
	});
}

function createVaccineAvailPlot(divName, vaccAvailPlotData) {
	var phrases = {0:'Vaccine',1:'Percent Availability',2:'Availability By Vaccine'}
	$.ajax({
		url:'json/translate',
		dataType:'json',
		data:phrases,
		type:"post",
		async:false,
		success:function(data){
			$('#' + divName).highcharts({
				chart : {
					type : 'bar',
					height : 200,
					width : 700
				},
				title : {
					text : data.translated_phrases[2]
				},
				legend : {
					enabled : false
				},
				xAxis : {
					categories : vaccAvailPlotData['categories'],
					title : {
						text : data.translated_phrases[0]
					}
				},
				yAxis : {
					min : 0,
					max : 109,
					endOnTick: false,
					title : {
						text : data.translated_phrases[1]
					}
				},
				plotOptions : {
					bar : {
						dataLabels : {
							enabled : true,
							format:'{y:.0f} %',
							crop: false,
							overflow:"none",
							
						}
					}
				},
				credits : {
					enabled : false
				},
				series : [{
					data : vaccAvailPlotData["plotData"]
				}]
			});
		}
	});
};
