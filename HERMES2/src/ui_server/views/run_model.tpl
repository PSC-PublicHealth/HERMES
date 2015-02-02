%rebase outer_wrapper title_slogan=_("Run A Model Simulation"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,developer=developer
<style>
.notification{
	padding:20px;
	position:absolute;
	top:40%;
	height:20%;
	width:30%;
	left:35%;
	background-color:#A0A3A6;
	color:white;
	font-weight:bold;
	opacity:0;
	z-index:100;
	display:none;
}
</style>

<h3>{{_('Running a HERMES Model')}}</h3>
<p>
<form>
  	<table>
  		<!--<tr>
  			<td><label for="run_model_id_select">{{_('Which model do you wish to run?')}}</label></td>
  			<td><select name="run_model_id_select" id="run_model_id_select"></select></td>
  		</tr>-->
	  	<tr>
  			<td>
  				<label for="run_results_name">{{_('What name should be given to this set of results?')}}</label>
  			</td>
  			<td>
  				<input type="text" name="run_results_name" id="run_results_name" \\
	%				if defined('runName'):
						value={{runName}} \\
	%				end
				>
			</td>
  		</tr>
  		<tr>
  			<td>
  				<label for="run_realizations">{{_('How many stochastic runs would you like to average the results over?')}}</label>
  			</td>
  			<td>
  				<input type="number" name="run_realizations" id="run_realizations" value=4>
  			</td>
  		</tr>
  		%if developer:
  			<tr>
  				<td>
  					<label for="deterministic_checkbox">{{_("Try to be deterministic?")}}</label>
  				</td>
	  			<td>
	  				<input type="checkbox" id="deterministic_checkbox"
		  			%if defined('deterministic') and deterministic:
		  			    checked
		  			%end
	  			    >
	  			</td>
  			</tr>
  		%end
  		%if developer:
  			<tr>
  				<td>
  					<label for="perfect_checkbox">{{_("Run with Perfect Storage and Transport?")}}</label>
  				</td>
	  			<td>
	  				<input type="checkbox" id="perfect_checkbox"
		  				%if defined('perfect') and perfect:
		  					checked
		  				%end
		  			>
		  		</td>
  			</tr>
  			<tr>
  				<td>
  					<label for="set_seeds_checkbox">{{_("Set random seeds?")}}</label>
  				</td>
  				<td>
  					<input type="checkbox" id="set_seeds_checkbox"
		  			%if defined('setseeds') and setseeds:
		  			    checked
		  			%end
		  			>
		  		</td>
	  			<td>
	  				<div id='subtable' 
			  			%if not defined('setseeds') or not setseeds:
			  				style='display:none'
			  			%end
			  		></div>
	  			</td>
  			</tr>
  		%end
  	</table>
</form>
<form id="run_parms_edit_form">
	<div id="run_parms_edit_form_div"></div>
</form>
 
<table width=100%>
  	<td width=10%>
  		<input type="button" id="cancel_button" value="{{_('Cancel')}}">
	</td>
	<td></td>
	<td width=10%>
		<input type="button" id="advanced_button" value="{{_('Show Advanced Paramters')}}">
	</td>
	<td width=10%>
		<input type="button" id="submit_button" value="{{_('Submit')}}">
	</td>
</table>

<div id="dialog-modal" title='{{_("Invalid Entry")}}'>
  <p>{{_("The name of the run results must not be blank.")}}</p>
</div>

<div id="validating-model-div" class="notification">
	<p>{{_("Please wait while HERMES validates your model prior to running.  This may take a few minutes so please be patient.")}}</p>
</div>

<div id="validating-model-dialog" title="{{_('Validating Model')}}">
	<table id="validation_report_grid"></table>
</div>

<div id="fatal-notify" title="{{_('Major Errors Exist')}}">
	<p>{{_('Your model has errors in it that could lead to erroneous results.')}}  
		{{_('You are free to still run the simulation but we would recommend that you click the button you Go To the Advanced Model Editor and correct these problems before proceeding')}}
	</p>
</div>

<div id="costing-notify" title="{{_('Major Costing Errors Exist')}}">
<p>{{_('Your model has costing errors in it that could lead to erroneous results.  You will not be able to run the simulation until this is corrected.')}}  
	{{_('You must correct these by editing the models costing page. Click the button at the bottom of the dialog labelled Go To Cost Model Editor to do this.')}}
</p>
</div>
<script>

$(function() {
	$("#fatal-notify").dialog({
		modal:true,
		autoOpen:false,
		width:300,
		height:300,
		buttons:{
			'{{_("Close")}}':function(){
				$(this).dialog("close");
			}
		}
	});
	$("#costing-notify").dialog({
		modal:true,
		autoOpen:false,
		width:300,
		height:300,
		buttons:{
			'{{_("Close")}}':function(){
				$(this).dialog("close");
			}
		}
	});
	
	$("#validating-model-div").corner();
	$("#validating-model-dialog").dialog({
		modal: true,
		autoOpen:false,
		width:'auto',
		height:'auto',
		buttons:{
			'{{_("Go To Advanced Model Editor")}}':function(){
				window.location = '{{rootPath}}model-edit-structure?id={{modelId}}';
			},
			'{{_("Go To Cost Model Editor")}}':function(){
				window.location = '{{rootPath}}cost-top?modelId={{modelId}}';
			},
			'{{_("Run Simulation")}}': function(){
				$(this).dialog("close");
				var dataToPass = {'modelId':{{modelId}},
						'runName':$("#run_results_name").val(),
						'deterministic':$("#deterministic_checkbox").is(':checked'),
						'nInstances':$("#run_realizations").val(),
						'perfect':$("#perfect_checkbox").is(':checked'),
						}
				var seedsChecked = $("#set_seeds_checkbox").is(":checked");
				dataToPass['setseeds'] = seedsChecked.toString();
				if(seedsChecked){
					for(var i=0;i<$("#run_realizations").val();i++){
						dataToPass['seed_'+i.toString()] = $("#seed_"+i.toString()).val().toString();
					}
				}
				
				var paramInputs = $('[id^=run_parms_edit_form_table] :input');
				run_params = {}
				for(var i =0;i<paramInputs.length;i++){
					run_params[paramInputs[i].id] = $("#"+paramInputs[i].id).val();
				}
				dataToPass['run_params'] = JSON.stringify(run_params)
				console.log(dataToPass);
				$.ajax({
					url:'{{rootPath}}json/run-start',
					datatype:'json',
					data:dataToPass,
					method:'post'
				})
				.done(function(result){
					if(!result.success){
						alert(result.msg);
					}
					else{
						window.location = "{{rootPath}}run-top";
					}
				})
				.fail(function(jqxhr, textStatus, error) {
		  			alert("Error: "+jqxhr.responseText);
				});
			}
		}
	});
	
	$("#dialog-modal").dialog({
		resizable: false,
      	modal: true,
		autoOpen:false,
     	buttons: {
			OK: function() {
				$( this ).dialog( "close" );
        	}
        }
	});
   
    $.ajax({
    	url: '{{rootPath}}model-run/json/run-parms-edit-form',
    	datatype:'json',
    	data:{'modelId':{{modelId}},'level':1,'maxLevel':2},
    })
    .done(function(data){
    	$("#run_parms_edit_form_div").html('<h3>' + data['title'] + '</h3>' + data['htmlstring']);
    })
    .fail(function(jqxhr, textStatus, error) {
    	alert("Error: " + jqxhr.responseText);
    });
    
    setParamVisibilityByLevel(1,"run_parms_edit_form_table");
    
    $("#submit_button").button();
    $("#submit_button").click(function(e){
    	//validate that the result has been given a name
    	$('.ui-dialog-buttonpane button:contains("Go To Advanced Model Editor")').button().hide();
    	$('.ui-dialog-buttonpane button:contains("Go To Cost Model Editor")').button().hide();
    	$('.ui-dialog-buttonpane button:contains("Run Simulation")').button().show();
    	if(validate_page()==true){
    		$("#validating-model-div").show().fadeTo(200,1.0);
    		$.ajax({
    			url:'{{rootPath}}json/run-validate-report?modelId={{modelId}}',
    			datatype:'json'
    		})
    		.done(function(results){
    			if(!results.success){
    				alert(results.msg);
    			}
    			else{
    				var hasFatals = false;
    				var hasCosting = false
    				for(var i=0;i<results.report.length;i++){
    					if(results.report[i]['messtype'] == 'Fatal Errors'){
    						hasFatals = true;
    						break;
    					}
    				}
    				for(var i=0;i<results.report.length;i++){
    					if(results.report[i]['messtype'] == 'Costing Errors'){
    						hasCosting = true;
    						break;
    					}
    				}
    				
    				$('#validation_report_grid').jqGrid({
    					datastr:results,
    					datatype:"jsonstring",
    					jsonReader: {
    						root:'report',
    						repeatitems: false,
    						id:'test'
    					},
    					width: 900,
    					height: 200,
    					rowNum:99999,
    					colNames:[
    						"{{_('Test')}}",
    						"{{_('Type')}}",
    						"{{_('Message')}}"
    					],
    					colModel:[
    					          {name:'test',index:'test',jsonmap:'testname',width:150},
    					          {name:'type',index:'type',jsonmap:'messtype',width:100},
    					          {name:'message',index:'message',jsonmap:'message',width:650}
    					],
    					loadtext:'Validating Model',
    					grouping:true,
    					groupingView: {
    						groupField: ['type'],
    						groupColumnShow: [false]
    					},
    					pager: "#validation_report_pager",
    					pgbuttons: false,
    					pgtext: null,
    					viewrecords: false
    				});
    				$("#validating-model-dialog").dialog("open");
    				
    				if(hasCosting){
    					$('.ui-dialog-buttonpane button:contains("Go To Cost Model Editor")').button().show();
    					$('.ui-dialog-buttonpane button:contains("Run Simulation")').button().hide();
    					$("#costing-notify").dialog("open");
    				}
    				if(hasFatals){
    					$('.ui-dialog-buttonpane button:contains("Go To Advanced Model Editor")').button().show();
    					$("#fatal-notify").dialog("open");
    				}
    			}
    			$("#validating-model-div").fadeTo(0.0).hide();
    		});
    	};
    });
    
    $("#cancel_button").button();
    $("#cancel_button").click(function(){
    	window.location = '{{breadcrumbPairs.getDoneURL()}}';
    });
    
    
    var btn = $("#advanced_button");
    btn.button();
    btn.attr('value','{{_("Show Advanced Options")}}');
    btn.click(function() {
    	if(btn.val() == "{{_('Show Advanced Options')}}"){
    		level = 2;
    		btn.attr('value','{{_("Show Basic Options")}}');
    	}
    	else{
    		level = 1;
    		btn.attr('value','{{_("Show Advanced Options")}}');
    	}
    	setParamVisibilityByLevel(level,"run_parms_edit_form_table");
    });
    
    $('#set_seeds_checkbox').click(function () {
		var nSeeds = $("#run_realizations").val();
		$("#subtable").html(generateSeedTable(nSeeds));
	    $("#subtable").toggle(this.checked);
	});	
	
	$('#run_realizations').change( function() {
		$("#subtable").html(generateSeedTable($(this).val()));
	});
});

function setParamVisibilityByLevel(level,table){
    $.ajax({
    	url:'json/run-parms-levels-to-show',
    	datatype:'json',
    	data:{'level':level}
    })
    .done(function(data) {
		if (data.success){
		    keyList = data['keyList']
		    $("#"+table+" :input").each( function(index) {
		       	var key = $(this).attr('id');
				if($.inArray(key,keyList) > -1){
				    $("#"+key).parent().parent().show();
				    $("#"+key).css("visibility","visible");
				}
				else{
				    $("#"+key).parent().parent().hide();
				}
		    });
		}
		else {
		    alert('{{_("Failed: ")}}' + data.msg);
		}
    })
    .fail(function(jqxhr, textStatus, error) {
    	alert("Error: " + jqxhr.responseText);
    });			
}

function generateSeedTable(nSlots) {
	var s = '<table>	<tr><th>{{_("Run")}}</th><th>{{_("Seed")}}</th></tr>';
	for (var i = 0; i < nSlots; i++) {
		s += '<tr><td>';
		s += (i+1).toString();
		var idStr = 'seed_'+i.toString();
		s += '</td><td><input type="number" id="'+idStr+'"></td></tr>';
	};
	s += '</table>';
	return s;
};


function validate_page(){
	if($("#run_results_name").val() == null || $("#run_results_name").val().length == 0){
		alert('{{_("Must give the run a name before proceeding")}}');
		return false;
	}
	
	return true;
};

</script>
 