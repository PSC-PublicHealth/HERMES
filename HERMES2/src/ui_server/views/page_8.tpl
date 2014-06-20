<div id='tabs-7'>

<body>	
<h2>{{_('Type Selector Tests')}}</h2>
<div align=center id="model_sel_widget"></div>
<div align=center>
  <select align=center id='typeselect'>
    <option value='fridges'>fridges</option>
    <option value='people'>people</option>
    <option value='trucks'>trucks</option>
    <option value='vaccines'>vaccines</option>
  </select>
</div>
<div align=center id="type_sel_widget"></div>
<script>

$(function() {
	$("#model_sel_widget").hrmWidget({
		widget:'modelSelector',
		label:'{{_("Showing types for")}}',
		afterBuild:function(mysel,mydata) {
			var modelId = this.modelSelector('selId');
			$("#type_sel_widget").hrmWidget({
				widget:'typeSelector',
				label:'{{_("Here are some things!")}}',
				invtype: function() { 
					return $('#typeselect').val()
				},
				modelId: function() { 
					return $('#model_sel_widget').modelSelector('selId') 
				},
				afterBuild:function(mysel) {
					alert('build!');
				},
				onChange:function(evt, typeName) {
					alert('change! '+typeName);
					return true;
				},
			});
		},
		onChange:function(mysel,mydata) {
			$("#type_sel_widget").typeSelector('rebuild');
		},
	});
});

$(function() {
	$('#typeselect').change(function(){ 
		$('#type_sel_widget').typeSelector('rebuild');
	})
});

</script>

</body>

</div>