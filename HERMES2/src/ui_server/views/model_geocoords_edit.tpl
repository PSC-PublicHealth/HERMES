%rebase outer_wrapper title_slogan=_('Edit Model Geographic Coordinates'),breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId
<!---
###################################################################################
# Copyright   2015, Pittsburgh Supercomputing Center (PSC).  All Rights Reserved. #
# =============================================================================== #
#                                                                                 #
# Permission to use, copy, and modify this software and its documentation without # 
# fee for personal use within your organization is hereby granted, provided that  #
# the above copyright notice is preserved in all copies and that the copyright    # 
# and this permission notice appear in supporting documentation.  All other       #
# restrictions and obligations are defined in the GNU Affero General Public       #
# License v3 (AGPL-3.0) located at http://www.gnu.org/licenses/agpl-3.0.html  A   #
# copy of the license is also provided in the top level of the source directory,  #
# in the file LICENSE.txt.                                                        #
#                                                                                 #
###################################################################################
-->
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
</style>
<input id="xlsupload" type="file" name="files[]" 
	data-url="{{rootPath}}upload-geocoordspreadsheet" style="display:none">

<script type="text/javascript" src="{{rootPath}}static/editor-widgets/geoCoordinateGrid.js"></script>
<h2>{{_("Edit the Geographic Coordinates for ")}}</h2>
<h4>
{{_("Please enter in the geographic coordinates of individual locations in the table below. Your entries will be saved automatically as you add them.")}}" +
</h4>
<br>
<div id = "geo_grid"></div>

<div id="uploadSpreadsheetDialog" href="#">
	<p>
	{{_("You can upload an excel file that contains the geographic coordinates of locations in your model.")}}
	{{_("Note, that this will be by location name, so if you have locations that have duplicate names, the algorithm will flag this and you will have to manually resolve.")}}
	</p>
	<p>{{_("Would you like to: ")}}
	<ul>
		<li>
			<a class="model-operation-item" id="downloadSpreadsheetLink">
				{{_("Download a preformated spreadhsheet for your model.")}}
			</a>
		</li>
		<li>
			<a class="model-operation-item" id="uploadSpreadsheetLink">
				{{_("Upload a completed spreadhsheet for your model.")}}
			</a>
		</li>
	</ul>
</div>

<div id="spreadupload-dialog" title='{{_("Upload Geocoordinate Spreadsheet")}}'>
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
			</table>
		</fieldset>
	</form>
</div>
<div id="spreadsheetbuttondiv">
	<button id="spreadsheetbutton">{{_('Upload a Spreadsheet')}}</button>
</div>
<div id="validSpread-dialog" title='{{_("Spreadsheet Validation Result")}}'> </div>
<div id="success-dialog" title='{{_("Spreadsheet Update Successful")}}'>{{_('Updating Geocoordates via Spreadsheet Successful')}}</div>
<script>

$("#spreadsheetbutton").button();
$("#uploadSpreadsheetDialog").dialog({
	resizable:false,
	model:true,
	autoOpen:false,
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
 	height: 300,
	width: 400,
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
    												           {name:'modelId',value:{{modelId}}}]
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
	url: "{{rootPath}}upload-geocoordspreadsheet",
	done: function(e,data){
		console.log(data.result);
		if(typeof data.result.files == 'undefined'){
			alert(data.result.message);
		}
		else if(data.result.validResult.success == false){
			alert("The Geographic Coordinate Spreadsheet failed validation: "+ data.result.validResult.message);
		}
		else{
			if(data.result.validResult.success){
				$.each(data.result.files, function(index,file) {
					$.ajax({
						url:'{{rootPath}}edit/verify-edit-geocoord-storegrid-from-json',
						method:'post',
						data:{
							'modelId':{{modelId}},
							'jsonStr':JSON.stringify(data.result.validResult.updates)
							},
						success: function(result){
							if(result.success){
								var htmlString = "<p>{{_('The updating of the geographic coordinates from the spreadsheet was successful')}}<p>";
								if(data.result.validResult.badNames.length > 0){
									htmlString += "<br><hr><br><p>There were some rows in the spreadsheet that were unable to be parsed:</p><br>";
									htmlString += "<ul>";
									for(var i=0;i<data.result.validResult.badNames.length;++i){
										htmlString += "<li>" + data.result.validResult.badNames[i][1] +"(" + data.result.validResult.badNames[i][0] 
													+ ") at level " + data.result.validResult.badNames[i][2] + "</li>";
									}
								}
								$("#geo_grid").geoCoordinateGrid("reloadGrid");
								$("#success-dialog").html(htmlString);
								$("#success-dialog").dialog("open");
							}
							else{
								alert("{{_('Didnot work')}}");
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



$("#geo_grid").geoCoordinateGrid({
	modelId:{{modelId}},
	rootPath:'{{rootPath}}'
});
$(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); });
</script>