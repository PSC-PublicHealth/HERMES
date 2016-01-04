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
<script type="text/javascript" src="{{rootPath}}static/editor-widgets/inventory_grid.js"></script>
<div id='store_edit_wgt_{{unique}}'>
<form id='store_edit_wgt_form_{{unique}}' action='json/throw-error'>
<ul>
	<li><a href='#store_edit_wgt_{{unique}}_tab1'>{{_("Main")}}</a></li>
	<li><a href='#store_edit_wgt_{{unique}}_tab7'>{{_("Costs")}}</a></li>
	<li><a href='#store_edit_wgt_{{unique}}_tab2'>{{_("Storage")}}</a></li>
	<!--
	<li><a href='#store_edit_wgt_{{unique}}_tab3'>{{_("Vaccines")}}</a></li>
	-->
	<li><a href='#store_edit_wgt_{{unique}}_tab4'>{{_("Transport")}}</a></li>
	<li><a href='#store_edit_wgt_{{unique}}_tab5'>{{_("Population")}}</a></li>
	<li><a href='#store_edit_wgt_{{unique}}_tab6'>{{_("Staff")}}</a></li>
</ul>
<div id='store_edit_wgt_{{unique}}_tab1'>
<table>
<tr>
		<td><label for='store_edit_wgt_f1_{{unique}}'>{{_("Name")}}</label></td>
		<td><input type=text class='sew_name_input' id='store_edit_wgt_f1_{{unique}}' name='name' value='{{storeName}}'></td>
		<td>({{idcode}})</td>
		<td>{{_("in ")+modelName+" (%d)"%modelId}}</td>
</tr>
<tr>
		<td><label for='store_edit_wgt_f5_{{unique}}'>{{_("Category")}}</label></td>
		<td><select class='sew_category_select' id='store_edit_wgt_f5_{{unique}}' name='category'>
	% for ln in levelNames:
	%   if ln==CATEGORY:
	  <option value='{{ln}}' selected>{{ln}}</option>
	%   else:
	  <option value='{{ln}}'>{{ln}}</option>
	%   end
	% end
		</select></td>
		<td><label for='store_edit_wgt_f6_{{unique}}'>{{_("Function")}}</label></td>
		<td><select class='sew_function_select' id='store_edit_wgt_f6_{{unique}}' name='function'>
	% for fn,tFn in functionNameTs:
	%   if fn==FUNCTION:
		  <option value='{{fn}}' selected>{{tFn}}</option>
	%   else:
		  <option value='{{fn}}'>{{tFn}}</option>
	%   end
	% end
	  </select></td>
</tr>
<tr>
		<td><label for='store_edit_wgt_f3_{{unique}}'>{{_("Latitude")}}</label></td>
		<td><input type=text class='sew_latitude_input' id='store_edit_wgt_f3_{{unique}}' name='latitude' value='{{Latitude}}' onkeypress="validateFloat(event)"></td>
		<td><label for='store_edit_wgt_f4_{{unique}}'>{{_("Longitude")}}</label></td>
		<td><input type=text class='sew_longitude_input' id='store_edit_wgt_f3_{{unique}}' name='longitude' value='{{Longitude}}' onkeypress="validateFloat(event)"></td>
</tr>
<tr>
		<td><label for='store_edit_wgt_f7_{{unique}}'>{{_("Treatment Session Interval")}}</label></td>
		<td><input type=text class='sew_useVialsInterval_input' id='store_edit_wgt_f7_{{unique}}' name='usevialsinterval' value='{{UseVialsInterval}}' onkeypress="validateFloat(event)"></td>
		<td><label for='store_edit_wgt_f8_{{unique}}'>{{_("Treatment Session Latency")}}</label></td>
		<td><input type=text class='sew_useVialsLatency_input' id='store_edit_wgt_f8_{{unique}}' name='usevialslatency' value='{{UseVialsLatency}}' onkeypress="validateFloat(event)"></td>
</tr>
<tr>
	<td><label for='store_edit_wgt_f9_{{unique}}'>{{_("Fraction Storage Available")}}</label></td>
	<td><input type=text class='sew_utilization_input' id='store_edit_wgt_f9_{{unique}}' name='utilizationrate' value='{{utilizationRate}}' onkeypress="validateFloat(event)"></td>
		<td><label for='store_edit_wgt_f2_{{unique}}'>{{_("Notes")}}</label></td>
		<td><input type=textfield class='sew_notes_input' id='store_edit_wgt_f2_{{unique}}' name='notes' value='{{Notes}}'></td>
</tr>
</table>
</div>
<div id='store_edit_wgt_{{unique}}_tab7'>
<table>
<tr>
<td><label for='store_edit_wgt_f10_{{unique}}'>{{_("Annual Cost")}}</label></td>
<td><input type=text class='sew_cost_input' id='store_edit_wgt_f10_{{unique}}' name='cost' value='{{cost}}'></td>
<td><div id='store_edit_wgt_cost_div_{{unique}}'></div>
</tr>
<tr>
<td><label for='store_edit_wgt_f11_{{unique}}'>{{_("in base year")}}</label></td>
<td><input type=text class='sew_cost_year_input' id='store_edit_wgt_f11_{{unique}}' name='costyear' value='{{costYear}}'></td>
<td></td>
</tr>
</table>
</div>
<div id='store_edit_wgt_{{unique}}_tab2'>
	<div id='store_edit_wgt_fridges_div_{{unique}}'></div>
	<!--<table id='store_edit_wgt_fridges_tbl_{{unique}}'></table>
	<div id='store_edit_wgt_fridges_tbl_pager_{{unique}}'></div>-->
</div>
<!--
<div id='store_edit_wgt_{{unique}}_tab3'>
	<table id='store_edit_wgt_vaccines_tbl_{{unique}}'></table>
	<div id='store_edit_wgt_vaccines_tbl_pager_{{unique}}'></div>
</div>
-->
<div id='store_edit_wgt_{{unique}}_tab4'>
	<div id='store_edit_wgt_trucks_div_{{unique}}'></div>
	<!--<table id='store_edit_wgt_trucks_tbl_{{unique}}'></table>
	<div id='store_edit_wgt_trucks_tbl_pager_{{unique}}'></div>-->
</div>
<div id='store_edit_wgt_{{unique}}_tab5'>
	<table id='store_edit_wgt_people_tbl_{{unique}}'></table>
	<div id='store_edit_wgt_people_tbl_pager_{{unique}}'></div>
</div>
<div id='store_edit_wgt_{{unique}}_tab6'>
	<table id='store_edit_wgt_staff_tbl_{{unique}}'></table>
	<div id='store_edit_wgt_staff_tbl_pager_{{unique}}'></div>
</div>
</form>
</div> 

<div id="store_type_info_dialog_{{unique}}" title="This should get replaced"></div>

<script>
% tS = _
% if defined('simpleTemplateDict'): _ = simpleTemplateDict
//% include flat_inventory_grid modelId=modelId,idcode=idcode,unique=unique,invtype='fridges',caption=tS('Cold Storage'),customCols=[(tS('Freezer (L)'),'freezer','freezer'), (tS('Cooler (L)'),'cooler','cooler'), (tS('Warm (L)'),'warm','roomtemperature')],loadonce=True,hiddengrid=False	
//% include flat_inventory_grid modelId=modelId,idcode=idcode,unique=unique,invtype='trucks',caption=tS('Transport'),customCols=[(tS('Cold Volume (L)'),'cooler','CoolVolumeL'), (tS('Storage'),'storage','Storage')],loadonce=True,hiddengrid=False
//% include flat_inventory_grid modelId=modelId,idcode=idcode,unique=unique,invtype='vaccines',caption=tS('Vaccines'),customCols=[(tS('Doses per vial'),'dosespervial','dosespervial'),(tS('Requires'),'requires','Requires')],loadonce=True,hiddengrid=False
% include flat_inventory_grid modelId=modelId,idcode=idcode,unique=unique,invtype='people',caption=tS('Client Population'),customCols=[],loadonce=True,hiddengrid=False
% include flat_inventory_grid modelId=modelId,idcode=idcode,unique=unique,invtype='staff',caption=tS('Local Staff'),customCols=[],loadonce=True,hiddengrid=False
% simpleTemplateDict = _
% _ = tS

$(function() {
	$('#store_edit_wgt_{{unique}}').tabs()

	$("#store_type_info_dialog_{{unique}}").dialog({autoOpen:false, height:"auto", width:"auto"});
	console.log("fuck");
	$("#store_edit_wgt_cost_div_{{unique}}").hrmWidget({
		 widget:'currencySelector',
		 modelId:{{modelId}},
		 label:'',
		 selected:"{{costCur}}"
	})
	
	$("#store_edit_wgt_fridges_div_{{unique}}").grid({
		modelId:{{modelId}},
		invType:"fridges",
		customCols:[
		            ['Freeser (L)','freezer','freezer'],
		            ['Cooler (L)','cooler','cooler'],
		            ['Warm (L)','warm','roomtemperature']
		           ],
		rootPath:'{{rootPath}}',
		idcode:{{idcode}},
		loadonce:true,
		//pagerId: 'store_edit_wgt_fridges_tbl_pager_{{unique}}',
		//infoDialogId:'store_type_info_dialog_{{unique}}',
		unique:{{unique}},
		editurl: '{{rootPath}}edit/store-edit-edit'
	});
	$("#store_edit_wgt_trucks_div_{{unique}}").grid({
		modelId:{{modelId}},
		invType:"trucks",
		customCols:[
		            ["Cold Volume (L)",'cooler','CoolVolumeL'],
		            ["Storage",'storage','Storage']
		           ],
		rootPath:'{{rootPath}}',
		idcode:{{idcode}},
		loadonce:true,
		//pagerId: 'store_edit_wgt_fridges_tbl_pager_{{unique}}',
		//infoDialogId:'store_type_info_dialog_{{unique}}',
		unique:{{unique}},
		editurl: '{{rootPath}}edit/store-edit-edit'
	});
	function getTypeData(grid) {
		var l = [];
		
		// Force a local save if necessary 
		var selrow = grid.jqGrid('getGridParam','selrow');
		if (selrow) grid.jqGrid("saveRow", selrow);
			
		var gridData = grid.jqGrid('getGridParam','data');
		var delData = grid.data('deletedRowList')
		for (var i in gridData) {
			var o = gridData[i];
			l.push( {typename:o['typestring'], visibletypename:o['visibletypestring'],
						count:o['count'], origcount:o['origcount']} );
		};
		if (typeof delData === "object") {
			for (var i in delData) {
				var o = delData[i];
				l.push( {typename:o, visibletypename:o, count:0} ); // fake a delete request
			};
			grid.data('deletedRowList',[]);
		}
		return l;
	};
	
	$("#store_edit_wgt_form_{{unique}}").submit( function(event) {
		event.preventDefault();
		$( this ).ajaxSubmit({
			data:{
				modelId:{{modelId}}, idcode:{{idcode}}, unique:{{unique}},
				costcur:$('#store_edit_wgt_cost_div_{{unique}}').currencySelector('selId'),
				fridgedata:getTypeData( $("#store_edit_wgt_fridges_tbl_{{unique}}") ),
				peopledata:getTypeData( $("#store_edit_wgt_people_tbl_{{unique}}") ),
				truckdata:getTypeData( $("#store_edit_wgt_trucks_tbl_{{unique}}") ),
				staffdata:getTypeData( $("#store_edit_wgt_staff_tbl_{{unique}}") )
			},
			url:'{{rootPath}}json/store-update',
			dataType:'json',
			type:'POST',
			success:(function(data) {
				var home = $("#store_edit_wgt_{{unique}}").parent();
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
