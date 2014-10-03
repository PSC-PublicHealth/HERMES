%rebase outer_wrapper **locals()

<table width=100%>
	<tr>
		<td colspan=2>
			<div align='center' id='model_sel_widget'></div>

			<div align='center' id='currency_sel_widget'></div>

			<div align='center' id='cost_base_year_div'>
			<label for="cost_base_year">{{_("Base Year")}}</label>
			<input type="number" min="{{minYear}}" max="{{maxYear}}" name="cost_base_year" id="cost_base_year">
			</div>

			<div align='center' id='cost_inflation_div'>
			<label for="cost_inflation">{{_("Inflation Rate")}}</label>
			<input type="number" min="-1000" max="1000" name="cost_inflation" id="cost_inflation">
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
					<td>{{_("Storage Equipment")}}</td><td><button id="cost_fridge_btn">{{_("Start")}}</button></td>
				</tr>
				<tr>
					<td>{{_("Storage Equipment version 2")}}</td><td><button id="cost_fridge2_btn">{{_("Start")}}</button></td>
				</tr>
				<tr>
					<td>{{_("Storage Equipment version 3")}}</td><td><button id="cost_fridge3_btn">{{_("Start")}}</button></td>
				</tr>
				<tr>
					<td>{{_("Vehicles")}}</td><td><button id="cost_truck_btn">{{_("Start")}}</button></td>
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
						<input type='checkbox' id='microcosting_enable_cbx'>
						<label for='microcosting_enable_cb'>{{_("Enable microcosting for this model?")}}</label>
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

{ // local scope

var buttonNames = ['fuel', 'truck', 'fridge', 'fridge2', 'fridge3', 'vaccine', 'salary', 'building'];

var getCurrentModelId = function(){ return $('#model_sel_widget').modelSelector('selId'); };
var getCurrentModelName = function(){ return $('#model_sel_widget').modelSelector('selName'); };

function buildPage() {
	$.getJSON('{{rootPath}}json/get-currency-info',{modelId:getCurrentModelId})
	.done(function(data) {
		if (data.success) {
			$("#currency_sel_widget").currencySelector('selId',data.baseCurrencyId);
			$("#cost_base_year").val(data.currencyBaseYear);
			$('#cost_inflation').val(data.priceInflation);
			$('#microcosting_enable_cbx').prop('checked', data.microCostingEnabled);
			for ( var i = 0; i<buttonNames.length; i++ ) {
				var lbl = data[buttonNames[i]+'Label'];
				if (lbl) $('#cost_'+buttonNames[i]+'_btn').button('option','label',lbl);
			}
		}
	    else {
	    	alert('{{_("Failed: ")}}'+data.msg);
	    }
	})
	.fail(function(jqxhr, textStatus, error) {
	    alert('{{_("Error: ")}}'+jqxhr.responseText);
	});
}


$(function() {
	{{!setupToolTips()}}
	
	$("#model_sel_widget").hrmWidget({
		widget:'modelSelector',
		label:'{{_("Showing costs for")}}',
		afterBuild:function(mysel,mydata) {
			$("#currency_sel_widget").hrmWidget({
				widget:'currencySelector',
				label:'{{_("Base Currency")}}',
				modelId:getCurrentModelId,
				afterBuild:function(mysel,mydata) { buildPage(); },
				onChange:function(mysel,mydata) {
					$.getJSON( '{{rootPath}}json/set-base-currency', {
						modelId:getCurrentModelId,
						id:function(){ return $('#currency_sel_widget').currencySelector('selId'); }
					})
					.done(function(data) {
						if ( data.success ) {
							$('#currency_sel_widget').currencySelector('save');
						}
						else {
							alert('{{_("Failed: ")}}'+data.msg);
							$('#currency_sel_widget').currencySelector('revert');
						}
					})
					.fail(function(jqxhr, textStatus, error) {
						alert("Error: "+jqxhr.responseText);
						$('#currency_sel_widget').currencySelector('revert');
					});
				}
			});
		},
		onChange:function(mysel,mydata) {
			$('#currency_sel_widget').currencySelector('rebuild');
		},
	});

	$('#cost_base_year').blur( function(evt) {
		$.getJSON('{{rootPath}}json/set-currency-base-year',
			{modelId:$('#model_sel_widget').modelSelector('selId'),
			baseYear:$('#cost_base_year').val()
		})
		.done(function(data) {
			if (data.success) {
				// do nothing
			}
    		else {
    			alert('{{_("Failed: ")}}'+data.msg);
    		}
		})
		.fail(function(jqxhr, textStatus, error) {
    		alert('{{_("Error: ")}}'+jqxhr.responseText);
		});
	})

	$('#cost_inflation').blur( function(evt) {
		$.getJSON('{{rootPath}}json/set-cost-inflation-percent',
				{modelId:$('#model_sel_widget').modelSelector('selId'),
				inflation:$('#cost_inflation').val()
		})
		.done(function(data) {
			if (data.success) {
				// do nothing
			}
    		else {
    			alert('{{_("Failed: ")}}'+data.msg);
    		}
		})
		.fail(function(jqxhr, textStatus, error) {
    		alert('{{_("Error: ")}}'+jqxhr.responseText);
		});
	})

	for ( var i = 0; i<buttonNames.length; i++ ) {
		$('#cost_'+buttonNames[i]+'_btn').button().click( function(evt) {
			var btnName = this.id.split('_')[1];
			window.location = "{{rootPath}}cost-edit-"+btnName;
			evt.preventDefault();
		});
	}
	
	$('#cost_check_completeness_btn').button().click( function(evt) {
		$.getJSON('{{rootPath}}json/cost-check-completeness',
				{ modelId:$('#model_sel_widget').modelSelector('selId')
		})
		.done(function(data){
			if (data.success) {
				if (data.value) {
					var dlgDiv = $('<div></div>');
					dlgDiv.append(data.msg);
					dlgDiv.dialog({
						autoOpen: true,
						modal: false,
						title: '{{_("The Costing Component is Ready")}}',
						close: function() { $(this).dialog('destroy'); },
						buttons: {
							'{{_("Ok")}}': function() {
								$(this).dialog("destroy");
							},
						}
					});
				}
				else {
					var dlgDiv = $('<div></div>');
					dlgDiv.append('{{!_("<b>The following problems remain:</b>")}}');
					dlgDiv.append('<ul>');
					for ( var i = 0; i<data.msgList.length; i++ ) {
						dlgDiv.append('<li>'+data.msgList[i]+'</li>');
					}
					dlgDiv.append('</ul>');
					dlgDiv.dialog({
						autoOpen: true,
						modal: false,
						title: '{{_("Cost Information is Incomplete")}}',
						close: function() { $(this).dialog('destroy'); },
						buttons: {
							'{{_("Ok")}}': function() {
								$(this).dialog("destroy");
							},
						}
					});
				}
			}
			else {
    			alert('{{_("Failed: ")}}'+data.msg);				
			}
		})
		.fail(function(jqxhr, textStatus, error) {
    		alert('{{_("Error: ")}}'+jqxhr.responseText);
		});		
	})
	
	$('#microcosting_enable_cbx').change( function(evt){
		$.getJSON('{{rootPath}}json/set-microcosting-enabled',
				{modelId:$('#model_sel_widget').modelSelector('selId'),
				 enabled:$(this).prop('checked')
		})
		.done(function(data){
			if (data.success) {
				$('#microcosting_enable_cbx').prop('checked', data.microCostingEnabled);			
			}
			else {
    			alert('{{_("Failed: ")}}'+data.msg);				
			}
		})
		.fail(function(jqxhr, textStatus, error) {
    		alert('{{_("Error: ")}}'+jqxhr.responseText);
		});		
	})
		
});

} // end local scope


</script>
 