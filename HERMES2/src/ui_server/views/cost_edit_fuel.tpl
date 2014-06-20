%rebase outer_wrapper **locals()

<table width=100%>
	<tr>
		<td colspan=2>
			<div align='center' id='model_sel_widget'></div>
			<div align='center' id='currency_sel_widget'></div>

		</td>
	</tr>
	<tr>
		<td width=100%>
			<div align='center'>
			<table>
				<tr>
					<th>{{_("Commodity")}}</th>
					<th>{{_("Price")}}</th>
					<th>{{_("Per")}}</th>
				</tr>
				
				<tr>
					<td>{{_("LP gas")}}</td>
					<td><input type='text' id='price_propane'></input></td>
					<td>{{_("Kg")}}</td>
				</tr>

				<tr>
					<td>{{_("Kerosene")}}</td>
					<td><input type='text' id='price_propane'></input></td>
					<td>{{_("Liter")}}</td>
				</tr>

				<tr>
					<td>{{_("Gasoline")}}</td>
					<td><input type='text' id='price_propane'></input></td>
					<td>{{_("Liter")}}</td>
				</tr>

				<tr>
					<td>{{_("Diesel")}}</td>
					<td><input type='text' id='price_propane'></input></td>
					<td>{{_("Liter")}}</td>
				</tr>

				<tr>
					<td>{{_("Electric Mains")}}</td>
					<td><input type='text' id='price_propane'></input></td>
					<td>{{_("Kilowatt Hour")}}</td>
				</tr>
			</table>
			</div>
		</td>
	</tr>
</table>
<form id="_edit_form">
    <div id="_edit_form_div"></div>
    <table width=100%>
      <tr>
        <td></td>
        <td width=10%><input type="button" id="cancel_button" value={{_("Cancel")}}></td>
        <td width=10%><input type="button" id="done_button" value={{_("Done")}}></td>
      </tr>
    </table>
</form>


<script>
$(function() {
	$("#model_sel_widget").hrmWidget({
		widget:'modelSelector',
		label:'{{_("Showing fuel costs for")}}',
		afterBuild:function(mysel,mydata) {

			// Build the currency selector, which depends on the model
			$("#currency_sel_widget").hrmWidget({
				widget:'currencySelector',
				label:'{{_("Prices are in")}}',
				modelId: function() {
					return $('#model_sel_widget').modelSelector('selId');
				},
				afterBuild:function(mysel,mydata) {
				},
				onChange:function(mysel,mydata) {
					return true; // which accepts the change
				},
			});

		},
		onChange:function(mysel,mydata) {
			// rebuild the currencySelector, which depends on the model
			$("#currency_sel_widget").currencySelector("rebuild");
		},
	});

	
	var buttonNames = ['fuel', 'power', 'truck', 'fridge', 'vaccine', 'salary', 'building'];
	for ( var i = 0; i<buttonNames.length; i++ ) {
		$('#cost_'+buttonNames[i]+'_btn').button().click( function(evt) {
			var btnName = this.id.split('_')[1];
			window.location = "{{rootPath}}cost_edit_"+btnName;
			evt.preventDefault();
		});
	}
});

</script>
 