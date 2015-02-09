%rebase outer_wrapper title_slogan=_('Model'),breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId

<style>
.loop_table_head{
	font-size:16px;
	font-weight:bold;
}
.loop_table_item{
	font-size:14px;
}
#generating_loops{
	padding:100px;
	position:absolute;
	top:40%;
	left:40%;
	background-color:#A0A3A6;
	color:white;
	font-weight:bold;
	opacity:0;
	z-index:100;
}
</style>

<h2>{{_("HERMES Transportation Loop Generator")}}</h2>
<h4>
{{_("Please enter in some key information about how loops are to be generated and then HERMES will transform your model by calculating the optimal transportation loops based on distance for your system between the two levels specified.")}}
</h4>

<div id="loop_form_div">
	<table style="width:500px">
		<tr class="loop_table_head">
			<td colspan=2>
				{{_("Loop Generator Options")}}
			</td>
		</tr>
		<tr class="loop_table_item">
			<td>
				{{_('Starting Supply Chain Level')}}
			</td>
			<td>
				<select id="levelfrom_select_box"></select>
			</td>
		</tr>
		<tr class="loop_table_item">
		<td>
			{{_('Ending Supply Chain Level')}}
		</td>
		<td>
			<select id="levelto_select_box"></select>
		</td>
	</tr>
		<tr class="loop_table_item">
			<td>
				{{_("Maximum Number of Locations Per Transport Loop")}}
			</td>
			<td>
				<input type="number" id="number_per_loop_input" value=3></input>
			</td>
		</tr>
		<tr class="loop_table_item">
			<td>
				{{_("Tranport Component to be Used for Loops")}}
			</td>
			<td>
				<select id="vehicle_select_box"></select>
			</td>
		</tr>
		<tr class="loop_table_item">
			<td colspan = 2>
				<div id="loop_submit_button">
					{{_('Generate Loops')}}
				</div>
	</table>
</div>
<div id="generating_loops">{{_('Generating Loops')}}</div>
<script>
$(function(){
	$('#loop_submit_button').button();
	$('#generating_loops').corner();
	$.ajax({
		url:'{{rootPath}}json/get-levels-in-model?modelId={{modelId}}',
		data:'json',
		success:function(result){
			if(!result.success){
				alert(result.msg);
			}
			for(var i=0;i<result.levels.length;i++){
				$("#levelfrom_select_box").append("<option value='"+result.levels[i]+"'>"+result.levels[i]+"</option>");
				$("#levelto_select_box").append("<option value='"+result.levels[i]+"'>"+result.levels[i]+"</option>");
			}
		}
	});
	
	$.ajax({
		url:'{{rootPath}}json/get-transport-type-names-in-model?modelId={{modelId}}',
		datatype:'json',
		success:function(result){
			if(!result.success){
				alert(result.msg);
			}
			for(var i=0;i<result.names.length;i++){
				$("#vehicle_select_box").append("<option value='"+result.values[i]+"'>"+
													result.names[i]+"</option>");
				
			}
		}
	});
	
	$('#loop_submit_button').click(function(){
		$('#generating_loops').fadeTo(300,1.0);
		$.ajax({
			url:'json/add-loops-to-model',
			dataType:'json',
			type:'post',
			data:{'modelId':{{modelId}},
				  'levelFrom':$('#levelfrom_select_box').val(),
				  'levelTo':$('#levelto_select_box').val(),
				  'numperloop':$('#number_per_loop_input').val(),
				  'vehicleToAdd':$("#vehicle_select_box").val()
				},
			success:function(result){
				if(!result.success){
					alert(result.msg);
				}
				else{
					$("generating_loops").fadeTo(300,0.0);
					window.location = '{{rootPath}}model-open?modelId={{modelId}}';
				}
			}
		
			
		})
	});
});

$(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); });

</script>

			