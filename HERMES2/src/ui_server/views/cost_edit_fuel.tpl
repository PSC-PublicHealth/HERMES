%rebase outer_wrapper **locals()
<!---
-->
<table width=100%>
	<tr>
		<td colspan=2>
			<div align='center' id='model_sel_widget'></div>
		</td>
	</tr>
	<tr>
		<td width=100%>
			<div align='center'>
			<table>
				<tr>
					<th>{{_("Commodity")}}</th>
					<th>{{_("Price")}}</th>
					<th></th>
					<th>{{_("Per")}}</th>
				</tr>
				
				<tr>
					<td>{{_("LP gas")}}</td>
					<td><input type='text' id='price_propane'></input></td>
					<td><div id='price_propane_units'></div></td>
					<td>{{_("Kg")}}</td>
				</tr>

				<tr>
					<td>{{_("Kerosene")}}</td>
					<td><input type='text' id='price_kerosene'></input></td>
					<td><div id='price_kerosene_units'></div></td>
					<td>{{_("Liter")}}</td>
				</tr>

				<tr>
					<td>{{_("Gasoline")}}</td>
					<td><input type='text' id='price_gasoline'></input></td>
					<td><div id='price_gasoline_units'></div></td>
					<td>{{_("Liter")}}</td>
				</tr>

				<tr>
					<td>{{_("Diesel")}}</td>
					<td><input type='text' id='price_diesel'></input></td>
					<td><div id='price_diesel_units'></div></td>
					<td>{{_("Liter")}}</td>
				</tr>

				<tr>
					<td>{{_("Electric Mains")}}</td>
					<td><input type='text' id='price_electric'></input></td>
					<td><div id='price_electric_units'></div></td>
					<td>{{_("Kilowatt Hour")}}</td>
				</tr>

				<tr>
				<td>{{_("Solar Power")}}</td>
				<td><input type='text' id='price_solar'></input></td>
				<td><div id='price_solar_units'></div></td>
				<td>{{_("Installed Kilowatt")}}</td>
			    </tr>

				<tr>
				<td>{{_("Ice")}}</td>
				<td><input type='text' id='price_ice'></input></td>
				<td><div id='price_ice_units'></div></td>
				<td>{{_("Freeze One Liter of Ice")}}</td>
			    </tr>
			    
				<tr>
				<td>{{!_("Solar Panel<br>Amortization")}}</td>
				<td><input type='text' id='price_solaramort'></input></td>
				<td>{{_("Years")}}</td>
			    </tr>

			</table>
			</div>
		</td>
	</tr>
</table>
<form id="_edit_form">
    <div id="_edit_form_div"></div>
</form>


<script>
{ // local scope

function buildPage(modelId) {
	$.getJSON('{{rootPath}}json/get-fuel-price-info',{ modelId:modelId })
	.done(function(data) {
		if (data.success) {
			var rowNames = ['propane', 'kerosene', 'gasoline', 'diesel', 'electric', 'solar', 'solaramort','ice'];
			for ( var i = 0; i<rowNames.length; i++ ) {
				var rowName = rowNames[i];
				function frzOnBlur(currentRowName) {
					return function(evt) {
						var units = null;
						if ($('#price_'+currentRowName+'_units').length)
							units = $('#price_'+currentRowName+'_units').currencySelector('selId');
						$.getJSON( '{{rootPath}}json/set-fuel-price/'+currentRowName, { 
							modelId:modelId,
							price:$('#price_'+currentRowName).val().unformatMoney(),
							id: units
						 })
						.done( function(data) {
							if (data.success) {
								var $priceEl = $('#price_'+currentRowName);
								var priceVal = data.price;
								if (data.price == null) $priceEl.val('');
								else $priceEl.val(data.price.formatMoney(2));
				    			$priceEl.floatTextBox('saveState');
							}
							else {
				    			alert('{{_("Failed: ")}}'+data.msg);
				    			$('#price_'+currentRowName).floatTextBox('revertState');
							}
						})
						.fail( function(jqxhr, textStatus, error) {
				    		alert('{{_("Error: ")}}'+jqxhr.responseText);
				    		$('#price_'+currentRowName).floatTextBox('revertState');
						});
					}
				};
				function frzCurSelChange(currentRowName) {
					return function(evt, currencyId) {
						$.getJSON('{{rootPath}}json/set-fuel-price-currency/'+currentRowName, {
							modelId:modelId,
							id:currencyId,
							price:$('#price_'+currentRowName).val().unformatMoney()
						})
						.done(function(data) {
							if ( data.success ) {
								if (data.id == currencyId) {
									$('#price_'+currentRowName+'_units').currencySelector('save');
									if (data.price) {
										$('#price_'+currentRowName).val( data.price.formatMoney(2) );
									}
								}
								else {
									alert( '{{_("Failed: Currency type mismatch")}}' );
									$('#price_'+currentRowName+'_units').currencySelector('revert');
								}
							}
							else {
								alert('{{_("Failed: ")}}'+data.msg);
								$('#price_'+currentRowName+'_units').currencySelector('revert');
							}
    					})
  						.fail(function(jqxhr, textStatus, error) {
  							alert("Error: "+jqxhr.responseText);
  							return false;
						});
					};
				};
				function frzFuelName(currentRowName) {
					return function() { return currentRowName; }
				};
				$('#price_'+rowName).hrmWidget({
					widget:'floatTextBox',
					onBlur:frzOnBlur(rowName)
				});
				if ($('#price_'+rowName+'_units').length) {
					var widgetArgs = {
							widget:'currencySelector',
							modelId:modelId,
							label:'',
							onChange:frzCurSelChange(rowName)
					};
					$('#price_'+rowName+'_units').hrmWidget( $.extend({},
							{selected:data[rowName+'Currency']},
							widgetArgs));					
					if (data[rowName+'Value'] != 'undefined' && data[rowName+'Value'] != null) {
						$('#price_'+rowName).val( data[rowName+'Value'].formatMoney(2) );
					}
					else {
						$('#price_'+rowName).val('');
					}
					$('#price_'+rowName).floatTextBox('saveState');
				}
				else {
					// There is no _units, so this is a simple scalar, not a real price
					if (data[rowName+'Value'] != 'undefined' && data[rowName+'Value'] != null) {
						$('#price_'+rowName).val( data[rowName+'Value'] );
					}
					else {
						$('#price_'+rowName).val('');
					}
					$('#price_'+rowName).floatTextBox('saveState');
					
				}
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
	$("#model_sel_widget").hrmWidget({
		widget:'modelSelector',
		label:'{{_("Showing fuel costs for")}}',
		writeable:true,
		afterBuild:function(mysel,mydata) {
			buildPage( mydata.selid );
		},
		onChange:function(evt, selId) {
			buildPage( selId );
			return true;
		},
	});
});

$(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); });

} // end local scope
</script>
 
