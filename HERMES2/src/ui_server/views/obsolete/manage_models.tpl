%rebase outer_wrapper title='Available Models',title_slogan='Available Models'

<h2>This is a file uploader</h2>
Drag-and-drop works; paste not so much.
<br>

<table id="manage_models_grid"></table>
<div id="manage_models_pager"> </div>


<input id="zipmodelupload" type="file" name="files[]" data-url="/bottle_hermes/upload-model" multiple>
<div id="progress">
    <div class="bar" style="width: 0%;"></div>
</div>


<div id="zipupload-dialog-form" title="Upload a Model in Zip Form">
  <p class="validateTips">All form fields are required.</p>
  <form>
  <fieldset>
    <label for="shortname">Name</label>
    <input type="text" name="shortname" id="shortname" class="text ui-widget-content ui-corner-all" />
  </fieldset>
  </form>
</div>

<script>
$("#manage_models_grid").jqGrid({ //set your grid id
   	url:'json/show-models-table',
	datatype: "json",
	width: 500, //specify width; optional
	colNames:['Id','Name','Select','Download Zip','Delete'], //define column names
	colModel:[
	{name:'id', index:'id', key: true, width:50},
	{name:'name', index:'name', width:100},
	{name:'select', index:'select', width:100},
	{name:'download zip', index:'downloadzip', width:100},
	{name:'delete', index:'delete', width:100},
	], //define column models
	pager: '#manage_models_pager', //set your pager div id
	sortname: 'name', //the column according to which data is to be sorted; optional
	viewrecords: true, //if true, displays the total number of records, etc. as: "View X to Y out of Z” optional
	sortorder: "asc", //sort order; optional
	gridview: true, // speeds things up- turn off for treegrid, subgrid, or afterinsertrow
    caption:"Available Models"
});

$(function () {
    $( "#zipupload-dialog-form" ).dialog({
    	autoOpen: false,
     	height: 300,
    	width: 350,
    	modal: true,
    	buttons: {
        	"Upload model": function() {
          		$("#shortname").removeClass( "ui-state-error" );
 
         		var bValid = true;
 				// We could validate shortname here
        		if ( bValid ) {
        			$( this ).data("confirm_me").formData = [ {name:'shortname', value:$("#shortname").val()} ];			
        			$( this ).data("confirm_me").submit();
            		$( this ).dialog( "close" );
          		}
        	},
        	Cancel: function() {
          		$( this ).dialog( "close" );
        	}
		},
      	close: function() {
        	$("#shortname").val( "" ).removeClass( "ui-state-error" );
		}
    });
 
    $('#zipmodelupload').fileupload({
        dataType: 'json',
        formData: [ { name: 'foo', value: 7}, {name: 'bar', value: 'baz'}, {name: 'shortname', value: 'myfile'}],
        add: function (e, data) {
        	$("#shortname").val(data.files[0].name);
        	console.log(data);
			$("#zipupload-dialog-form").data("confirm_me",data).dialog("open");
		},
        done: function (e, data) {
        	if (typeof data.result.files == 'undefined') {
        		alert(data.result.message);
        	}
        	else {
        		$.each(data.result.files, function (index, file) {
        			alert( 'got '+file.name+' '+file.size+' bytes');
        		});
        	}
		},
	    progressall: function (e, data) {
  			var progress = parseInt(data.loaded / data.total * 100, 10);
        	$('#progress .bar').css('width',progress + '%');
        }
    });

});
</script>
