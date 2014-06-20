<div id='tabs-7'>

<body>	
<h2>{{_('Route Editor Tests')}}</h2>

<table>
<tr>
<td colspan=2><div id="model_sel_widget2"></div></td>
</tr>
<tr>
<td><label for="route_name">{{_("Route Name")}}</label></td>
<td><input type="text" id="route_name"></td>
</tr>
</table>

<button id="testbutton">{{_('Do it!')}}</button>

<div id='test_route_edit_div'></div>
<script>

$(function() {
	$("#model_sel_widget2").hrmWidget({
		widget:'modelSelector',
		label:'{{_("Showing routes for")}}',
		afterBuild:function(mysel,mydata) {
			var modelId = this.modelSelector('selId');
		},
		onChange:function(mysel,mydata) {
			/*
			$("#type_sel_widget").typeSelector('rebuild');
			*/
			return true;
		},
	});
});

$(function() {
	$('#test_route_edit_div').data('kidcount',0);
	var btn = $("#testbutton");
	btn.button();
	btn.click( function() {
		var count = $('#test_route_edit_div').data('kidcount');
		count += 1;
		$('#test_route_edit_div').data('kidcount',count);
		var divId = "test_route_edit_kid"+count.toString();
		var $newdiv = $( "<div id='"+divId+"' />" );
		var innerDivId = "inner_"+divId;
		$('#test_route_edit_div').append($newdiv);
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
			widget:'routeEditor',
			modelId:$("#model_sel_widget2").modelSelector('selId'),
			routename:$("#route_name").val(),
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
        $newdiv.dialog('option','title',"Editing route "+$("#route_name").val()+" of model "+$("#model_sel_widget2").modelSelector('selName'));
	});
});

</script>

</body>

</div>