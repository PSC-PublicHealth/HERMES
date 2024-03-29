%rebase outer_wrapper title_slogan=_('Edit Model Population Demand Estimates'),breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,name=name
<!---
-->
<script type="text/javascript" src="{{rootPath}}static/jquery.fileDownload.js"></script>
<style>
.model-operation-title{
	font-size:20px;
	font-weight:bold;
}
.model-operation-second{
	font-size:11px;
}
a.model-operation-item:link{
	font-size:14px;
	color:#282A57;
}
a.model-operation-item:visited{
	font-size:14px;
	color:#282A57;
}
.large_dialog_font{
	font-size:16px;
	font-family:'Century Gothic', Arial, 'Arial Unicode MS', Helvetica, Sans-Serif;
}
.large_dialog_font p{
	padding:10px;
	text-align:center;
}
</style>
<input id="xlsupload" type="file" name="files[]" 
	data-url="{{rootPath}}upload-populationspreadsheet" style="display:none">

<script type="text/javascript" src="{{rootPath}}static/editor-widgets/popDemandGrid.js"></script>
<h2>{{_("Edit the Population Estimates for the {0} Model".format(name))}}</h2>
<h4>
{{_("Please enter in the population estimates for the number individuals of each type to be vaccinated during a year at individual locations in the table below. Your entries will be saved automatically as you add them.")}}</h4>
<br>
<div id = "pop_grid"></div>

<div id="uploadSpreadsheetDialog">
	<span class="large_dialog_font">
		<p>
			{{_("You can upload an excel file that contains the population estimates of locations in your model.")}}
		</p>
		<p> 
			{{_('Would you like to')}} 
		</p>
		<p style="margin-left:10px;">
			<a href="#" id="download_choice">{{_("Download a Preformatted Spreadsheet")}}</a>
		</p>
		<p>	
			{{_('or')}}
		</p>
		<p style="margin-left:10px;">
			<a href="#" id="upload_choice">{{_("Upload a Completed Spreadsheet?")}} </a>
		</p>
	</span>
</div>

<div id="spreadupload-dialog" title='{{_("Upload Population Demand Spreadsheet")}}'>
<p>{{_("Please tell us where the spreadsheet it.")}}
	<form>
		<fieldset>
			<input type='hidden' name='shortname' id='shortname' />
			<table>
				<tr>
					<td>
						<label for="filename">{{_('File')}}</label>
					</td>
					<td>
						<input id="xlsfilename" type="file" name="files[]" accept="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet">
					</td>
				</tr>
				<tr>
				<td>
					{{_('Would you like to override the Location Names with those in your spreadsheet?')}}
				</td>
				<td>
					<input id='override-names-checkbox' type="checkbox">
				</td>
			</tr>
			</table>
		</fieldset>
	</form>
</div>
<div id="spreadsheetbuttondiv">
	<button id="spreadsheetbutton">{{_('Download a Template/Upload a Spreadsheet')}}</button>
</div>
<div id="validSpread-dialog" title='{{_("Spreadsheet Validation Result")}}'> </div>
<div id="success-dialog" title='{{_("Spreadsheet Update Successful")}}'>{{_('Updating Population Demand Estimates via Spreadsheet Successful')}}</div>
<div id="down-success-dialog" title="{{_('Template Download Successful')}}">
	{{_("The Template Spreadsheet has been saved, please check your browser's Download folder to access and then upload when you are finished.")}}
</div>

<script>

$("#spreadsheetbutton").button();

$("#spreadsheetbutton").click(function(){
		$("#uploadSpreadsheetDialog").dialog("open");
});

$("#upload_choice").click(function(){
	$("#uploadSpreadsheetDialog").dialog("close");
	$("#spreadupload-dialog").dialog("open");
});

$("#download_choice").click(function(){
	$.fileDownload('{{rootPath}}downloadTemplatePopulationXLS?modelId={{modelId}}',{
		successCallback: function(url){
			$("#uploadSpreadsheetDialog").dialog("close");
			$("#down-success-dialog").dialog("open");
		},
		failCallback: function(html,url){
			alert('Your file download just failed for this URL:' + url + '\r\n' +
	                'Here was the resulting error HTML: \r\n' + html);
		}
	});
});

$("#uploadSpreadsheetDialog").dialog({
	resizable:false,
	model:true,
	autoOpen:false,
	width:'auto',
	buttons:{
		'{{_("Close")}}':function(){
			$(this).dialog("close");
		}
	},
	open: function(e,ui) {
	    $(this)[0].onkeypress = function(e) {
			if (e.keyCode == $.ui.keyCode.ENTER) {
			    e.preventDefault();
			    $(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
			}
	    };
	}
});

$("#down-success-dialog").dialog({
	resizable:false,
	model:true,
	autoOpen:false,
	width:'auto',
	buttons:{
		'{{_("OK")}}':function(){
			$(this).dialog("close");
		}
	},
	open: function(e,ui) {
	    $(this)[0].onkeypress = function(e) {
			if (e.keyCode == $.ui.keyCode.ENTER) {
			    e.preventDefault();
			    $(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
			}
	    };
	}
});
$("#success-dialog").dialog({
	resizable:false,
	model:true,
	autoOpen:false,
	buttons:{
		'{{_("OK")}}':function(){
			$(this).dialog("close");
		}
	},
	open: function(e,ui) {
	    $(this)[0].onkeypress = function(e) {
			if (e.keyCode == $.ui.keyCode.ENTER) {
			    e.preventDefault();
			    $(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
			}
	    };
	}
});

$("#validSpread-dialog").dialog({
	resizable:false,
	model:true,
	autoOpen:false,
	buttons:{
		'{{_("Continue")}}':function(){
			//$
		},
		'{{_("Cancel")}}':function(){
			$(this).dialog("close");
		}
	},
	open: function(e,ui) {
	    $(this)[0].onkeypress = function(e) {
			if (e.keyCode == $.ui.keyCode.ENTER) {
			    e.preventDefault();
			    $(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
			}
	    };
	}
});

$( "#spreadupload-dialog" ).dialog({
	autoOpen: false,
 	height: 'auto',
	width: 'auto',
	modal: true,
	buttons: {
    	'OK': {
    		text: '{{_("Upload XLS")}}',
    		click: function() {
    			//Error Checking
    			if(!$("#xlsfilename").val()){
    				alert("{{_('Must specify an excel file to upload.')}}");
    			}
    			else{
    				var files = $("#xlsfilename").prop('files');
    				$("#shortname").val($("#xlsfilename").val().replace(/^.*[\\\/]/, ''));
    				$("#xlsupload").fileupload('add',{files:files,
    												 formData:[{name:'shortname',value:$("#shortname").val()},
    												           {name:'modelId',value:{{modelId}}},
    												           {name:'overrideNames',value:$("#override-names-checkbox").is(":checked")}]
    												}
    				);
    				
    			}
    			$("#spreadupload-dialog").dialog("close");
    		}
    	},
    	'CANCEL':{
    		text:'{{_("Cancel")}}',
    		click: function(){
    			$(this).dialog("close");
    		}
    	}
    },
	close: function() {
    	$("#xlsfilename").val('');
	},
	open: function(e,ui) {
		$(this)[0].onkeypress = function(e) {
			if (e.keyCode == $.ui.keyCode.ENTER) {
				e.preventDefault();
				$(this).parent().find('.ui-dialog-buttonpane button:first').trigger('click');
			}
	    };
	}
});

$("#xlsupload").fileupload({
	dataType:'json',
	formData:[],
	autoUpload:true,
	url: "{{rootPath}}upload-populationspreadsheet",
	done: function(e,data){
		console.log(data.result);
		if(typeof data.result.files == 'undefined'){
			alert(data.result.message);
		}
		else if(data.result.validResult.success == false){
			alert("{{_('The Population Estimates Spreadsheet failed validation: ')}}"+ data.result.validResult.message);
		}
		else{
			if(data.result.validResult.success){
				$.each(data.result.files, function(index,file) {
					$.ajax({
						url:'{{rootPath}}edit/verify-edit-population-storegrid-from-json',
						method:'post',
						data:{
							'modelId':{{modelId}},
							'jsonStr':JSON.stringify(data.result.validResult.updates),
							'overrideNames':$("#override-names-checkbox").is(":checked")
							},
						success: function(result){
							if(result.success){
								var htmlString = "<p>{{_('The updating of the population estimates from the spreadsheet was successful')}}<p>";
								if(data.result.validResult.badNames.length > 0){
									htmlString += "<br><hr><br><p>{{_('There were some rows in the spreadsheet that were unable to be parsed:')}}</p><br>";
									htmlString += "<ul>";
									for(var i=0;i<data.result.validResult.badNames.length;++i){
										htmlString += "<li>" + data.result.validResult.badNames[i][1] +"(" + data.result.validResult.badNames[i][0] 
													+ ") at level " + data.result.validResult.badNames[i][2] + "</li>";
									}
								}
								$("#pop_grid").popDemandGrid("reloadGrid");
								$("#success-dialog").html(htmlString);
								$("#success-dialog").dialog("open");
							}
							else{
								alert("{{_('Did not work')}}");
							}
						},
						error: function(jqxhr, textStatus, errorThrown) {
							alert('{{_("Error: ")}}'+jqxhr.responseText);
				        }
					});
				});
			}
			$('#ajax_busy').hide();	
		}
	}
});

console.log([
% for i in range(0,len(popTypeNames)):
	"{{popTypeNames[i]}}",
%end
]);
$("#pop_grid").popDemandGrid({
	modelId:{{modelId}},
	rootPath:'{{rootPath}}',
	popHeads:[
% for i in range(0,len(popTypeNames)):
	"{{popTypeNames[i][1]}}",
%end
	],         
	popCats:[
% for i in range(0,len(popTypeNames)):
	"{{popTypeNames[i][0]}}",
%end
	]
});
$(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); });
</script>
