<div id='tabs-12'>

<body>	
<h2>{{_('This edits types in-place')}}</h2>
Warning: this can invalidate runs and create type naming discrepancies!  Only minimal checking is performed on the submitted values!
<p>
<div id='model_sel_widget'></div>

<label>Which Category?</label>
<select id='type_class_sel_div'>
<option value="fridges">Fridges</option>
<option value="trucks">Trucks</option>
<option value="vaccines">Vaccines</option>
<option value="people">People</option>
<option value="staff">Staff</option>
</select>
<div id='type_sel_div'></div>
<button id='edit_button'>Edit</button>
<div id='edit_form_div'></div>
<table width=100%>
<tr>
  <td width=10%><input type="button" id="cancel_button" value={{_("Cancel")}}></td>
  <td width=10%><input type="button" id="done_button" value={{_("Save")}}></td>
  <td></td>
</tr>
</table>
<script>



$(function() {
	function updatePage(modelId) {
		$('#type_sel_div').typeSelector('rebuild');
	};

	$("#type_class_sel_div").change(function() {
		var modelId = $('#model_sel_widget').modelSelector('selId');
		updatePage(modelId);
	});
	
	$("#model_sel_widget").hrmWidget({
		widget:'modelSelector',
		label:'{{_("Which Model?")}}',
		afterBuild:function(mysel,mydata) {
			$('#type_sel_div').hrmWidget({
				widget:'typeSelector',
				modelId:function() { return $('#model_sel_widget').modelSelector('selId'); },
				invtype:function() { return $('#type_class_sel_div').val(); },
				label:'{{_("Which Type?")}}'
			});
		},
		onChange:function(evt, selId) {
			updatePage( selId );
			return true;
		},
	});
	
	function loadForm() {
		$('#edit_form_div').empty();
		var modelId = $('#model_sel_widget').modelSelector('selId');
		var typeName = $('#type_sel_div').typeSelector('selValue');
		$.getJSON('json/type-edit-form',{
			typename:typeName, 
			modelId:modelId
			})
		.done(function(data) {
			if (data.success) {
				$("#edit_form_div").hrmWidget({
					widget:'editFormManager',
					html:data['htmlstring'],
					modelId:modelId
				});			
			}
			else {
				alert('{{_("Failed: ")}}'+data.msg);
			}

		})
		.fail(function(jqxhr, textStatus, error) {
			alert("Error: "+jqxhr.responseText);
		});		
	};
	
	function saveForm() {
		var dict = $('#edit_form_div').editFormManager('getEntries');
		$.getJSON("{{rootPath}}json/type-edit-verify-commit",dict)
		.done(function(data) {
			if (data.success) {
				if (data.value) {
					alert('saved');
				}
				else {
					alert(data['msg']);
				}
			}
			else {
				alert('{{_("Failed: ")}}'+data.msg);
			}
    	})
  		.fail(function(jqxhr, textStatus, error) {
  			alert("Error: "+jqxhr.responseText);
		});
	};
	
	$("#edit_button").button().click(function() {
		loadForm();
	});

	$("#cancel_button").button().click( function() {
		loadForm();
	});
	
	$('#done_button').button().click( function() {
		saveForm();
	});
});


</script>

</body>

</div>