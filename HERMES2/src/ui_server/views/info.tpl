%rebase outer_wrapper title_slogan='About HERMES',_=_,inlizer=inlizer,breadcrumbPairs=breadcrumbPairs
<!---
-->

<style>
.bulletted_list{
	margin-left: 5em;
	margin-right:5em;
	list-style-type: circle;
}
.ui-tabs.ui-tabs-vertical {
    padding: 0;
    width: 90%
}
.ui-tabs.ui-tabs-vertical .ui-widget-header {
    border: none;
}
.ui-tabs.ui-tabs-vertical .ui-tabs-nav {
    float: left;
    width: 15em;
    background: #CCC;
    border-radius: 4px 0 0 4px;
    border-right: 1px solid gray;
}
.ui-tabs.ui-tabs-vertical .ui-tabs-nav li {
    clear: left;
    width: 100%;
    margin: 0.2em 0;
    border: 1px solid gray;
    border-width: 1px 0 1px 1px;
    border-radius: 4px 0 0 4px;
    overflow: hidden;
    position: relative;
    right: -2px;
    z-index: 2;
}
.ui-tabs.ui-tabs-vertical .ui-tabs-nav li a {
    display: block;
    width: 100%;
    padding: 0.6em 1em;
}
.ui-tabs.ui-tabs-vertical .ui-tabs-nav li a:hover {
    cursor: pointer;
}
.ui-tabs.ui-tabs-vertical .ui-tabs-nav li.ui-tabs-active {
    margin-bottom: 0.2em;
    padding-bottom: 0;
    border-right: 1px solid white;
}
.ui-tabs.ui-tabs-vertical .ui-tabs-nav li:last-child {
    margin-bottom: 10px;
}
.ui-tabs.ui-tabs-vertical .ui-tabs-panel {
    float: left;
    width: 75%;
    border-left: 1px solid gray;
    border-radius: 0;
    position: relative;
    left: -1px;
}
.option_em{
	font-weight:bold;
	color:#5053AF;
}
</style>
<div id="main_help_tabs">
	<ul>
		<li><a href="#help_overview">{{_("Overview")}}</a></li>
		<li><a href="#help_welcome_page">{{_("The Welcome Page")}}</a></li>
		<li><a href="#help_available_models_page">{{_("Available Models Page")}}</a></li>
		<li><a href="#help_create_a_model">{{_("Create A New Model")}}</a></li>
	</ul>
	<div id="help_overview">
		<p>
			<h2>Overview of HERMES</h2>
			<hr>
		  	<strong>HERMES</strong>, or the Highly Extensible Resource for Modeling Event-Driven Supply Chains, 
		  	is a software platform that allows users to generate a detailed discrete event simulation model of any vaccine 
		  	supply chain. This simulation model can serve as a "virtual laboratory" for decision makers (e.g., policy makers, 
		  	health officials, funders, investors, vaccine and other technology developers, manufacturers, distributors, 
		  	logisticians, scientists, and researchers) to address a variety of questions such as:
		  </p>
	
		  <ul class="bulletted_list">
			  <li>{{_('What will be the impact of introducing new technologies (e.g., vaccines, storage, or monitoring)?')}}</li>
			  <li>{{_('What the effects of altering the characteristics of vaccines and other technologies (e.g., vaccine vial size, vaccine thermostability, or cold device capacity)?')}}</li>
			  <li>{{_('How do the configuration and the operations of the supply chain (e.g., storage devices, shipping frequency, personnel, or ordering policy) affect performance and cost?')}}</li>
			  <li>{{_('What may be the effects of differing conditions and circumstances (e.g., power outages, delays, inclement weather, transport breakdown, or limited access)?')}}</li>
			  <li>{{_('How should one invest or allocate resources (e.g., adding refrigerators vs. increasing transport frequency)?')}}</li>
			  <li>{{_('How can vaccine delivery be optimized (e.g., minimize the cost per immunized child or maximize immunization availability)?')}}</li>
		  </ul>
		
		  <p>
		  	The model can represent every storage location, immunization location, storage device, transport vehicle/device,
		  		personnel, vaccine vial, and vaccine accessory in a supply chain. The model represents each vaccine vial, diluent vial, 
			  or vaccine accessory with an entity, which can assume a variety of characteristics such as type, size, number of doses per 
			  vial, temperature profile, age, and expiration date.  Millions of different vaccine vials and accessories can flow through 
			  the model simultaneously just like a real supply chain. There is practically no limit to the number of vaccines, storage 
			  locations, devices, and vehicles that the model can simulate.
		  </p>
		
		 
		  <p>
		  	At each immunization location, virtual people arrive each day when they are ready to 
			  receive a particular vaccine or set of vaccines. The policy at that location determines when the health workers 
			  open vaccine vials and, if necessary, reconstitute the vaccines. (The user can specify policies for each immunization 
			  location). The client arrival rates can come from either actual demand data or census plus birth data. If the 
			  correct vaccine is available at the immunization location then the person is successfully immunized. If the vaccine 
			  is not available, then the person counts as a missed vaccination opportunity. Once an immunization occurs, the remaining 
			  vial and accessories count as medical waste. Unused doses in open vaccine vials count as open vial wastage.
		  </p>
	 </div>
	 <div id="help_welcome_page">
	 	<h2>The Welcome Page</h2>
	 	<hr>
	 	<p>
			When HERMES is initially opened, the user is presented with the <span class="option_em">Welcome Page</span> which provides you with a few options of tasks to do with HERMES.  
			Clicking on any of these options will take you to a new page that will give you the ability to do the task. Please click on one of these options to begin.
		</p>
		
		<p>The options are:</p>
		<hr>
		<h3>
			Create or Upload a New Model
		</h3>
		<p>
			When this is selected, a dialog will appear that will ask you whether they would like to 
			<span class="option_em">Create a New Model</span> or 
			<span class="option_em">Upload an Exisiting Model from a HERMES Zip File</span>.  If <span class="option_em">Create a New Model</span> is selected, you will be taken to the beginning of 
			the <span class="option_em">Create a New Model Workflow</span>, where you will be taken through a series of steps to define a new model. If <span class="option_em">Upload an Exisiting Model from a HERMES Zip File</span>
			is selected, you will be presented with a dialog box. Clicking on the <span class="option_em">Choose File</span> button will open a window to explore your computer's directories to specify where the HERMES Zip
			file exists.  You can give the uploaded model any name you would like (by default, the name will mimic the zip file's name).  Once both of these are selected
			then you can click the <span class="option_em">Upload model</span> button and the model will be uploaded to the HERMES Database.  Once the zip is successfully uploaded, you will be notified by a dialog, and you can click <span class="option_em">OK</span>.
			You can navigate to the <span class="option_em"><a href="#help_available_models_page" class="open-tab">Availables Models</a></span> page to open and use the model.
		</p>
		<p>
		Please note, that if you try to upload an invalid zip file that does not conform to the HERMES inputs, you will be notified that the upload failed, and no model will be uploaded to the HERMES Database.
		</p>
		<hr>
		<p><b>Open, Modify, and Run an Exisiting Model</b></p>
		<p>
			When this is selected, a new page will open that lists all of the models that are currently available in your installation of HERMES.
			For each model, there is a line in the list with its name, its ID, a place for Notes, and several buttons that define actions that you can 
			perform on the model.
		</p>	
	</div>
	<div id="help_available_models_page">
		<p>
			<b>To Change the name or add notes to the model</b> you can double click on the line of the model you wish to change and a dialog box will
			open that gives you a place to put the new name and some notes.  Once you are finished editing, can click the Save button, and you list will be 
			updated with the new information.
		</p>
		<p>
			On each line, there are a series of action buttons which will perform various operations on the model in that line.
		</p>
		<p>
			<b>The "Open" Button</b> will take you the "Model Page" where you will be able to perform more detailed tasks on the model such as editing 
			and running simulations.
		</p>
		<p>
			<b>The "Run" Button</b> will open the "Run Simulations Page" which will allow you to set up and execute a simulation run with this model.
		</p>
		<p>
			<b>The "Results" Button</b> will be active if simulations have been performed with this model. If there are no results for this model yet, 
			then the button will be faded and greyed out until there are results available.
		</p>
	</div>
	<div id="help_create_a_model">
		There shoudl be help here
	</div>
</div>

<script>
$(document).ready(function(){
	$("#main_help_tabs").tabs()
		.addClass('ui-tabs-vertical ui-helper-clearfix');
	
	$('.open-tab').click(function (event) {
	    var tab = $(this).attr('href');
	    var index = $(tab).parent().index();
	    //console.log(tab.attr('tabindex'));
	    $('#main_help_tabs').tabs('option','active',index);
	});
});
</script>
