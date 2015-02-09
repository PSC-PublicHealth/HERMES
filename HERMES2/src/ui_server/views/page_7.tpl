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
<div id='tabs-7'>

<body>	
<h2>{{_('Store Editor Tests')}}</h2>
<table>
<tr>
<td><label for="model_id">{{_("Model Id")}}</label></td>
<td><input type="number" min="1" id="model_id"></td>
</tr>
<tr>
<td><label for="store_idcode">{{_("Store idcode")}}</label></td>
<td><input type="number" min="1" id="store_idcode"></td>
</tr>
</table>

<button id="testbutton">{{_('Do it!')}}</button>

<div id=test_store_edit_div></div>

<script>

$(function () {
	$('#test_store_edit_div').data('kidcount',0);
	var btn = $("#testbutton");
	btn.button();
	btn.click( function() {
		var count = $('#test_store_edit_div').data('kidcount');
		count += 1;
		$('#test_store_edit_div').data('kidcount',count);
		var divId = "test_store_edit_kid"+count.toString();
		var $newdiv = $( "<div id='"+divId+"' />" );
		var innerDivId = "inner_"+divId;
		$('#test_store_edit_div').append($newdiv);
		$newdiv.dialog({
			autoOpen:false, 
			height:"auto", 
			width:"auto",
			buttons: {
	    		Ok: function() {
					$( this ).find('form').submit();
		    	},
	    		Cancel: function() {
	      			$( this ).dialog( "close" );
	    		}
			}
		});
		$newdiv.html( "<div id='"+innerDivId+"' />" );
		$('#'+innerDivId).hrmWidget({
			widget:'storeEditor',
			modelId:$("#model_id").val(),
			idcode:$("#store_idcode").val(),
			closeOnSuccess:divId,
			callbackData:{foo:'hello',bar:'world'},
			afterBuild:function() { 
				$newdiv.dialog('open'); 
			},
            onServerSuccess: function(data, cbData) { 
            	alert('server success '); 
            	console.log(cbData);
            }			
		});
        $newdiv.dialog('option','title',"Editing location "+$("#store_idcode").val()+" of model "+$("#model_id").val());
	});
});
</script>

</body>

</div>