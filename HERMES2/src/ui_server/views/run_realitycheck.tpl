%rebase outer_wrapper title_slogan=_("Run A Model Simulation"), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer
<h3>{{_('Model Validation Stage')}}</h3>
<br>

<div id="validation_report_div">
	<button id="proc_validation_button" style="width:200px;">{{_("Validate Model")}}</button>
	<div id="validation_report_pager"></div>
	<table id="validation_report_grid"></table>
</div>
<form>
    <table width=100%>
      <tr>
        <td width 10%><input type="button" id="back_button" value={{_("Back")}}></td>
        <td></td>
        <td width=10%><input type="button" id="next_button" value={{_("Next")}}></td>
      </tr>
    </table>
</form>

<script>

$(function() {
	var btn = $("#back_button");
	btn.button();
	btn.click( function() {
		window.location = "{{rootPath}}model-run/back"
	});

	var btn = $("#next_button");
	btn.button();
	btn.click( function() {
		window.location = "{{rootPath}}model-run/next";
	});
	
});

$(document).ready(function(){
	$("#proc_validation_button").click( function(){
		this.style.visibility='hidden';
		$('#validation_report_grid').jqGrid({
			url:"{{rootPath}}json/run-validate-report?modelId={{get('modelId')}}",
			datatype:"json",
			jsonReader: {
				root:'report',
				repeatitems: false,
				id:'test'
			},
			caption:"{{_('Model Validation Results For {0}').format(modelName)}}",
			width: 900,
			height: 200,
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
		$("#validation_report_grid").jqGrid('navGrid','#validation_report_pager',{edit:false,add:false,del:false,search:false,refresh:false});
		// setup grid print capability. Add print button to navigation bar and bind to click.
		setPrintGrid('validation_report_grid','validation_report_pager','{{_("Validation Issues")}}');
	});
	
});

</script>
 