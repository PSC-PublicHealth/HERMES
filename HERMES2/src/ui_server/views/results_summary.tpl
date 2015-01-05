%rebase outer_wrapper title_slogan=_('Simulation Results'), breadcrumbPairs=breadcrumbPairs,_=_,inlizer=inlizer,modelId=modelId,resultsId=resultsId

<script type="text/javascript" src="{{rootPath}}static/Highcharts-3.0.5/js/highcharts.js"></script>
<script type="text/javascript" src="{{rootPath}}static/jquery.fileDownload.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/summary.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/vaccine_availability_by_cohort.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/storage_utilization_by_level.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/transport_utilization_by_route.js"></script>
<script type="text/javascript" src="{{rootPath}}static/results-widgets/vaccine_summary_grid.js"></script>

<link rel="stylesheet" href='{{rootPath}}static/results-widgets/results-widgets.css'/> 

<h1>{{modelName}}</h1>

<h4>Results: {{resultsGroupName}}</h4>

<div id="summary_test_div" class='rs_summary' width="100%"/>
    
<div id="summary_div" width="100%">
    <table id="vaccine_summary_results_grid"></table>
    <div style="width:500;" id="results_summary_buttons_div">
        <button id="results_summary_show_ge_button" style="width:100px;">{{_('Show Geographic Viz')}}</button>
        <button id="results_summary_show_ne_button" style="width:100px;">{{_('Show Network Viz')}}</button>
        % if gvAvailable:
        <button id="results_summary_show_gv_button" style="width:100px;">{{_('Show Fireworks Viz')}}</button>
        % end
        <button id="results_download_xls_button" style="width:100px;">{{_('Download Excel Results')}}</button>
    </div>
    <div style="float:left;width:300;" id="vaccine-availability-by-cohort"></div>
    <div style="float:left;width:300;" id="storage-utilization-by-level"></div>
    <div style="float:left;width:300;" id="transUtil_by_route_graph"></div>
</div>

<div id="download_xls_saveas" title={{_('Save Excel Model Results As...')}}>
	<form>
		<fieldset>
			<table>
				<tr>
					<td><label for="download_xls_saveas_name">{{_('Filename')}}</td>
					<td><input id="download_xls_saveas_name" type="text"></td>
				</tr>
			</table>
		</fieldset>
	</form>
</div>











