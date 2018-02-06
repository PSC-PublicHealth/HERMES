<!---
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
-->
<div id='route_edit_wgt_{{unique}}'>
<form id='route_edit_wgt_form_{{unique}}' action='json/throw-error'>
<ul>
	<li><a href='#route_edit_wgt_{{unique}}_tab1'>{{_("Main")}}</a></li>
	<li><a href='#route_edit_wgt_{{unique}}_tab2'>{{_("Stops")}}</a></li>
</ul>
<div id='route_edit_wgt_{{unique}}_tab1'>
	<table>
	<tr>
		<td><label>{{_("Route Type")}}</label></td>
		<td><div id='routetype_select_div_{{unique}}'></div></td>
		<td><label>{{_('Transport Mode')}}</label></td>
		<td><div id='truck_select_div_{{unique}}'></div></td>
	</tr>
	<tr>
  		<td><label for='route_edit_wgt_f3_{{unique}}'>{{_("Shipping Interval")}}</label></td>
  		<td><input type='text' id='route_edit_wgt_f3_{{unique}}' name='shipintervaldays' value='{{ShipIntervalDays}}' onkeypress="validateFloat(event)"></td>
  		<td><label for='route_edit_wgt_f4_{{unique}}'>{{_("Shipping Latency")}}</label></td>
  		<td><input type='text' id='route_edit_wgt_f4_{{unique}}' name='shiplatencydays' value='{{ShipLatencyDays}}' onkeypress="validateFloat(event)"></td>
	</tr>
	<tr>
		<td><label for='route_edit_wgt_f5_{{unique}}'>{{_("Route Conditions")}}</label></td>
		<td><input type='text' id='route_edit_wgt_f5_{{unique}}' name='conditions' value='{{Conditions}}'></td>
		<td><label for='route_edit_wgt_f6_{{unique}}' id='route_edit_wgt_l6_{{unique}}' style="display:none">{{_("On-Demand Order Days")}}</label></td>
		<td><input type='text' id='route_edit_wgt_f6_{{unique}}' name='pullorderamountdays' value='{{PullOrderAmountDays}}' onkeypress="validateFloat(event)" style="display:none"></td>
	</tr>
	<tr>
		<td><label>{{_('Per Diem Rule')}}</label></td>
		<td><div id='perdiem_select_div_{{unique}}'></div></td>
	</tr>
	</table>
</div>

<div id='route_edit_wgt_{{unique}}_tab2'>
	<table id='route_edit_wgt_stops_tbl_{{unique}}'></table>
	<div id='route_edit_wgt_stops_tbl_pager_{{unique}}'></div>
</div>

</form>
</div> 

<script>
% tS = _
% if defined('simpleTemplateDict'): _ = simpleTemplateDict
% simpleTemplateDict = _
% _ = tS

$(function() {
	var routeIsScheduled = {
	% for k,v in routeTypeIsScheduledDict.items():
		{{k}}:{{'true' if v else 'false'}},
	% end
	};
	
	$('#route_edit_wgt_{{unique}}').tabs();
	
	$('#route_edit_wgt_l6_{{unique}}').toggle(( ! routeIsScheduled['{{routeType}}'] ));
	$('#route_edit_wgt_f6_{{unique}}').toggle(( ! routeIsScheduled['{{routeType}}'] ));
	
	$('#routetype_select_div_{{unique}}').hrmWidget({
		widget:'routeTypeSelector',
		label:'',
		selected:'{{routeType}}',
		onChange: function(evt,typeName) {
			var nRows = $('#route_edit_wgt_stops_tbl_{{unique}}').jqGrid('getGridParam','records');
			if ( (nRows != 2) && (typeName == 'attached' || !routeIsScheduled[typeName]) ) {
				alert('{{_("On-demand routes can only support one supplier and one client.")}}');
				return false;
			}
			else {
				var pullOptionsVisible = ( ! routeIsScheduled[typeName] );
				$('#route_edit_wgt_l6_{{unique}}').toggle(pullOptionsVisible);
				$('#route_edit_wgt_f6_{{unique}}').toggle(pullOptionsVisible);

				$('#route_edit_wgt_stops_tbl_{{unique}}').trigger('reloadGrid');
				return true;
			}
		}
	});
	
	$('#truck_select_div_{{unique}}').hrmWidget({
		widget:'typeSelector',
		label:'',
		invtype:'trucks',
		modelId:{{modelId}},
		selected:'{{truckType}}',
		canBeBlank:true
	});

	$("#perdiem_select_div_{{unique}}").hrmWidget({
		widget:'simpleTypeSelectField',
		modelId:{{modelId}},
		invType:'perdiems',
		persistent:true,
		maxHeight:300
	});
	
//	$('#perdiem_select_div_{{unique}}').hrmWidget({
//		widget:'typeSelector',
//		label:'',
//		invtype:'perdiems',
//		modelId:{{modelId}},
//		selected:'{{perdiemType}}',
//		canBeBlank:true
//	});

	$('#route_edit_wgt_stops_tbl_{{unique}}').jqGrid({
   		url:'{{rootPath}}json/route-edit-manage-stop-table',
		editurl: 'clientArray',
		datatype: "json",
		postData: {
			modelId: {{modelId}},
			routename: '{{routeName}}',
			routetype: function() { return $('#routetype_select_div_{{unique}}').routeTypeSelector('selValue'); }
		},
		width: 740, //specify width; optional
		colNames:[
			"{{_('Name')}}",
			"{{_('ID')}}",
			"{{_('Hours to Next Stop')}}",
			"{{_('KM to Next Stop')}}",
			""
		], //define column names
		colModel:[
			{name:'name', index:'name', width:200, sortable:false},
			{name:'idcode', index:'idcode', width:70, sortable:false, align:'center', key:true},
			{name:'triptime', index:'triptime', width:70, sortable:false, editable:true, edittype:'text', editrules:{number:true}},
			{name:'tripkm', index:'tripkm', width:70, sortable:false, editable:true, edittype:'text', editrules:{number:true}},
			{name:'info', index:'info', width:200, align:'left', sortable:false}
		], //define column models
		scroll: true,
		gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
    	caption:'{{_("Stops along this route")}}',
		loadError: function(xhr,status,error){
			alert('{{_("Error: ")}}'+status);
		},
		beforeProcessing: function(data,status,xhr) {
			if (!data.success) {
				alert('{{_("Failed: ")}}'+data.msg);
			}
		},
		onSelectRow: function(resultsid, status){
   			if (resultsid) {
				var $this = $(this);
				$this.jqGrid('editRow',resultsid,{
					keys:true,
					extraparam: { 
						modelId: {{modelId}},
						routename: '{{routeName}}',
						routetype: function() { return $('#routetype_select_div_{{unique}}').routeTypeSelector('selValue'); }
					},
					successfunc: function(response) {
						if (response.status >=200 && response.status<300) {
							data = $.parseJSON(response.responseText);
							if (data.success == undefined) return true;
							else {
								if (data.success) return true;
								else {
									if (data.msg != undefined) alert(data.msg);
									else alert('{{_("Sorry, transaction failed.")}}');
									return false;
								}
							}
						}
						else {
							alert('{{_("Sorry, transaction failed.")}}');
							return false;
						}
					}
				});
   			}
   		},
   	gridComplete: function(){
      var $this = $(this);
      // resize grid to fit dialog
    	var uaSpecificWidth = 0; //default tested on Firefox
    	var uaSpecificHeight = 0;
    	if (navigator.userAgent.match(/webkit/i)) {
        uaSpecificWidth = 0;   //Webkit specific
        uaSpecificHeight = 4;
      }
      var gridParentDialog = $(this).parent().parent().parent().parent().parent().parent().parent().parent().parent();
    	gridParentDialog.bind("dialogresize", function () {
        $this.jqGrid('setGridWidth', gridParentDialog.width()-uaSpecificWidth-40);
        $this.jqGrid('setGridHeight', gridParentDialog.height()-uaSpecificHeight-120);
    	});
   	}
	});
	
	var grid = $('#route_edit_wgt_stops_tbl_{{unique}}'), headerRow, rowHight, resizeSpanHeight;
	// get the header row which contains
	headerRow = grid.closest("div.ui-jqgrid-view")
    	.find("table.ui-jqgrid-htable>thead>tr.ui-jqgrid-labels");

	// increase the height of the resizing span
	resizeSpanHeight = 'height: ' + headerRow.height() +
    	'px !important; cursor: col-resize;';
	headerRow.find("span.ui-jqgrid-resize").each(function () {
    	this.style.cssText = resizeSpanHeight;
	});

	// set position of the dive with the column header text to the middle
	rowHight = headerRow.height();
	headerRow.find("div.ui-jqgrid-sortable").each(function () {
    	var ts = $(this);
    	ts.css('top', (rowHight - ts.outerHeight()) / 2 + 'px');
	});

	function getStopData(grid) {
		var l = [];
		
		// Force a local save if necessary 
		var selrow = grid.jqGrid('getGridParam','selrow');
		if (selrow) grid.jqGrid("saveRow", selrow);
		
		var gridData = grid.jqGrid('getGridParam','data');
		var gridData = grid.jqGrid('getRowData');
		for (var i in gridData) {
			var o = gridData[i];
			l.push( {name:o['name'], idcode:o['idcode'],
					triptime:o['triptime'], tripkm:o['tripkm']} );
		};
		return l;
	};
	
	$("#route_edit_wgt_form_{{unique}}").submit( function(event) {
		event.preventDefault();
		$( this ).ajaxSubmit({
			data:{
				modelId:{{modelId}}, routename:'{{routeName}}', unique:{{unique}},
				routeType:function(){ return $('#routetype_select_div_{{unique}}').routeTypeSelector('selValue'); },
				truckType:function(){ return $('#truck_select_div_{{unique}}').typeSelector('selValue'); },
				stopdata:getStopData( $("#route_edit_wgt_stops_tbl_{{unique}}") ),
				perdiemType:function(){ return $('#perdiem_select_div_{{unique}}').typeSelector('selValue'); }
			},
			url:'{{rootPath}}json/route-update',
			dataType:'json',
			type:'POST',
			success:(function(data) {
				var home = $("#route_edit_wgt_{{unique}}").parent();
				var opFuncs = home.data('opFuncs');
	    		if (data.success) {
					if (data.value) {
						% if defined('closeOnSuccess'):
						$("#{{closeOnSuccess}}").dialog('close');
						% end
						if (opFuncs && opFuncs.onServerSuccess) opFuncs.onServerSuccess.bind(home.first())(data,opFuncs.callbackData);
					}
					else {
						alert(data['msg']);
						if (opFuncs && opFuncs.onServerError) opFuncs.onServerError.bind(home.first())(data,opFuncs.callbackData);
					}
	    		}
	    		else {
	    			alert('{{_("Failed: ")}}'+data.msg);
					if (opFuncs && opFuncs.onServerFail) opFuncs.onServerFail.bind(home.first())(data,opFuncs.callbackData);
	    		}
			}),
			error:  (function(jqxhr, textStatus, error) {
	    		alert('{{_("Error: ")}}'+jqxhr.responseText);
			})
		});
	});
});
</script>
