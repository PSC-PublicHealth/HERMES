%rebase outer_wrapper **locals()

<table width=100%>
	<tr>
		<td colspan=2>
			<div align='center' id='model_sel_widget'></div>

			<div align='center' id='cost_base_year_div'>
			<label for="cost_base_year">{{_("Cost base year")}}</label>
			<input type="number" min="2000" max="2100" name="cost_base_year" id="cost_base_year">
			</div>

			<div align='center' id='cost_inflation_div'>
			<label for="cost_inflation">{{_("Inflation Rate")}}</label>
			<input type="number" min="2000" max="2100" name="cost_inflation" id="cost_inflation">
			<label for="cost_inflation">{{_("Percent")}}</label>
			</div>

		</td>
	</tr>
	<tr>
		<td>
			<table width='100%' class='hrm_btn_table'>
				<tr>
					<th colspan=2>Cost Components</th>
				</tr>

				<tr>
					<td><label for="cost_fuel_btn">{{_("Fuel and Power")}}</label></td>
					<td><button id="cost_fuel_btn">{{_("Start")}}</button></td>
				</tr>
				<tr>
					<td>{{_("Vehicles")}}</td><td><button id="cost_truck_btn">{{_("Start")}}</button></td>
				</tr>
				<tr>
					<td>{{_("Storage Equipment")}}</td><td><button id="cost_fridge_btn">{{_("Start")}}</button></td>
				</tr>
				<tr>
					<td>{{_("Vaccines")}}</td><td><button id="cost_vaccine_btn">{{_("Start")}}</button></td>
				</tr>
				<tr>
					<td>{{_("Salaries and Per Diem")}}</td><td><button id="cost_salary_btn">{{_("Start")}}</button></td>
				</tr>
				<tr>
					<td>{{_("Buildings")}}</td><td><button id="cost_building_btn">{{_("Start")}}</button></td>
				</tr>
			</table>
		</td>
		<td>
			<table>
				<tr>
					<td>
						Some kind of status<br>info goes here?
					</td>
 				</tr>
 				<tr>
					<td rowspan=2><button id="cost_check_completeness_btn">{{_("Check Completeness")}}</button>
 				</tr>
			</table>
		</td>
	</tr>
</table>


<script>
{{!setupToolTips()}}

$(function() {
	$("#model_sel_widget").hrmWidget({
		widget:'modelSelector',
		label:'{{_("Showing costs for")}}',
		afterBuild:function(mysel,mydata) {
			var modelId = this.modelSelector('selId');
			var modelName = this.modelSelector('selName');
			// put more code here
		},
		onChange:function(mysel,mydata) {
			var modelId = this.modelSelector('selId');
			var modelName = this.modelSelector('selName');
			// put more code here
		},
	});
	
	var buttonNames = ['fuel', 'truck', 'fridge', 'vaccine', 'salary', 'building'];
	for ( var i = 0; i<buttonNames.length; i++ ) {
		$('#cost_'+buttonNames[i]+'_btn').button().click( function(evt) {
			var btnName = this.id.split('_')[1];
			window.location = "{{rootPath}}cost-edit-"+btnName;
			evt.preventDefault();
		});
	}
	$('#cost_check_completeness_btn').button().click( function(evt) {
			window.location = "{{rootPath}}cost-check-complete";
			evt.preventDefault();
		});;
});

</script>
 