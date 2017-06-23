%rebase outer_wrapper **locals()
<!---
###################################################################################
# Copyright   2017, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
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
<div>
<table width=100%>
  <tr>
    <td>
    	<table class='hrm_centered_pairs'>
			<tr>
			  <td><label for="model_sel_widget">{{_('Showing Factory for')}}</label></td>
			  <td><div align='center' id='model_sel_widget'></div></td>
			</tr>
			<tr class="factory_uneditable">
			  <td colspan=2>{{_("This model has manufacturers which is not currently supported graphical user interface.  Currently they can only be edited by downloading the model and editing the CSV files.")}}
			  </td>
			</tr>
			<tr class="factory_editable">
			  <td>
			    <input type='checkbox' id='factory_enable_cbx' onclick="factory_click_cbx(this)">
			    <label for='factory_enable_cb'>{{_("Override default of unlimited factory production for this model?")}}</label>
			  </td>
		 	</tr>
			<tr class="factory_enabled">
			  <td><label for="factory_latency">{{_("Startup Latency")}}</label></td>
			  <td><input type="number" min="0" max="10000" name="factory_latency" id="factory_latency">
			    <label for="factory_latency">{{_("Days")}}</label></td>
			</tr>
			<tr class="factory_enabled">
			  <td><label for="factory_interval">{{_("Production Interval")}}</label></td>
			  <td><input type="number" min="1" max="10000" name="factory_interval" id="factory_interval">
			    <label for="factory_interval">{{_("Days")}}</label></td>
			</tr>
			<tr class="factory_enabled">
			  <td><label for="factory_overstock">{{_("Overstock Factor")}}</label></td>
			  <td><input type="number" min="0" max="1000" name="factory_overstock" id="factory_overstock">
			    <label for="factory_overstock">{{_("Percent")}}</label></td>
			</tr>
			<tr class="factory_enabled">
			  <td><label for="factory_demandtype">{{_("Production Calculation Method (demand type)")}}</label></td>
			  <td><select id="factory_demandtype">
			      <option value="projection" selected>projection</option>
			      <option value="expectation">expectation</option>
			    </select>
			  </td>
			</tr>
			<tr class="factory_editable">
			  <td colspan=2>
			    <button id="factory_update" onclick="update_factory()">{{_("Update Factory")}}</button>
			  </td>
			</tr>
		</table>
    </td>
  </tr>
</table>
</div>
<script>
var getCurrentModelId = function(){ return $('#model_sel_widget').modelSelector('selId'); };
var getCurrentModelName = function(){ return $('#model_sel_widget').modelSelector('selName'); };
var mode = "uneditable"

function setVisibility() {
    if (mode == "uneditable") {
	$('.factory_uneditable').each(function() {
	    $(this).css('display', 'block');
	});
	$('.factory_editable').each(function() {
	    $(this).css('display', 'none');
	});
	$('.factory_enabled').each(function() {
	    $(this).css('display', 'none');
	});
    }
    if (mode == "editable") {
	$('.factory_uneditable').each(function() {
	    $(this).css('display', 'none');
	});
	$('.factory_editable').each(function() {
	    $(this).css('display', 'block');
	});
	$('.factory_enabled').each(function() {
	    $(this).css('display', 'none');
	});
    }
    if (mode == "enabled") {
	$('.factory_uneditable').each(function() {
	    $(this).css('display', 'none');
	});
	$('.factory_editable').each(function() {
	    $(this).css('display', 'block');
	});
	$('.factory_enabled').each(function() {
	    $(this).css('display', 'block');
	});
    }
}

function fillInFieldData(data) {
    if (!data.editable) {
	mode = "uneditable";
	setVisibility();
	return;
    }

    if (data.factoryCount > 1) {
	mode = "uneditable";
	setVisibility();
	return;
    }
	
    if (data.factoryCount == 0) {
	document.getElementById("factory_enable_cbx").checked = false;
	mode = "editable";
	setVisibility();
	return;
    }

    if (data.factoryCount == 1) {
	document.getElementById("factory_enable_cbx").checked = true;
	document.getElementById("factory_latency").value = data.latency;
	document.getElementById("factory_interval").value = data.intervalDays;
	document.getElementById("factory_overstock").value = data.overstock;
	var element = document.getElementById("factory_demandtype");
	for (var i = 0; element.options[i]; ++i) {
	    if (element.options[i].value == data.demandType) {
	    	element.selectedIndex = i;
	    }
	}
	mode = "enabled";
	setVisibility();
	return;
    }	
}


function getFieldData() {
    $.getJSON( '{{rootPath}}json/get-factory-data', {modelId:getCurrentModelId, })
	.done(function(data) {
	    if ( data.success ) {
		fillInFieldData(data);
	    }
	    else {
		alert('{{_("Failed: ")}}'+data.msg);
		fillInFieldData({editable:false});
	    }
	})
	.fail(function(jqxhr, textStatus, error) {
	    alert("Error: "+jqxhr.responseText);
	});
}
$(function() {
	{{!setupToolTips()}}
	
	$("#model_sel_widget").hrmWidget({
		widget:'modelSelector',
		label:'',
		writeable:true,
		afterBuild:function(mysel,mydata) {
		    getFieldData();
		},
		onChange:function(mysel,mydata) {
		    getFieldData();
		},
	});
});

function factory_click_cbx(element) {
    if (mode == "editable") {
	data = {editable:true, factoryCount:1, latency:0, intervalDays:28, overstock:133, demandType:"projection"};
	fillInFieldData(data);
    } else {
	data = {editable:true, factoryCount:0};
	fillInFieldData(data);
    }
}

function update_factory() {
    if (mode == "editable") {
	data = { factoryCount:0 };
    } else {
	data = { factoryCount:1,
		 latency: document.getElementById("factory_latency").value,
		 intervalDays: document.getElementById("factory_interval").value,
		 overstock: document.getElementById("factory_overstock").value,
		 demandType: document.getElementById("factory_demandtype").value }
    }
    data.modelId = getCurrentModelId
    //alert(JSON.stringify(data))

    $.getJSON('{{rootPath}}json/set-factory-data', data)
	.done(function(data) {
	    if ( data.success ) {
	    }
	    else {
		alert('{{_("Failed: ")}}'+data.msg);
	    }
	})
	.fail(function(jqxhr, textStatus, error) {
	    alert("Error: "+jqxhr.responseText);
	});
}

$(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); });
</script>
