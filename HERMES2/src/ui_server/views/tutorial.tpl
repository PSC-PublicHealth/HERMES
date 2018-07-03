%rebase outer_wrapper _=_,title_slogan=_('HERMES Graphical User Inferface Start'),inlizer=inlizer,breadcrumbPairs=breadcrumbPairs
<!---
-->
<style>
#sp_top_div{
	position: relative;
	width:"100%";
	top: 0px;
	left: 0px;
	border-style: none;
	border-width: 2px;
	text-align: left;
}
#sp_content_div{
	position: relative;
	width:80%;
	float:none;
	margin: 0 auto;
}

</style>

			
<div id="sp_top_div" class="sp_top_div">
	<div id="sp_content_div" class="content_div">
			
			<p><h1 style="text-align:left">{{_("HERMES User Interface Tutorial")}}</h1></p>
			<p> {{_("HERMES is a software platform that allows users to generate a detailed discrete event simulation model of any healthcare supply chain. This simulation model can serve as a \"virtual laboratory\" for decision makers (e.g., policy makers, health officials, funders, investors, vaccine and other technology developers, manufacturers, distributors, logisticians, scientists, and researchers) to address a variety of important questions.")}}</p>

			<p>{{_("HERMES simulates a given supply chain's locations and equipment, transport routes, the employees who staff these locations and transport routes, and the patients who receive the healthcare product in question. To do this, the user inputs information or selects from a variety of pre-programmed options. The resulting models can answer a variety of questions, displaying results in many different graphical and tabular formats.")}}
			</p>

			<p>{{_("The following is a brief exercise to get you familiar with the the HERMES User Interface and perform a simple experiment on an already established model. Click on the \"?\" icon in the top right corner of any page for additional help.")}}</p>
			
			<p><h2>{{_("Exercise 1: Modify and Run an Existing Model  (Addition of Rotarix Vaccine) ")}}</h2></p>

			<h3>{{_("Making a Copy of the Gaza Province, Mozambique Model")}}</h3>
			
			<p>{{_("To start using HERMES, you'll be modifying an existing model of the vaccine supply chain in Gaza Province, Mozambique. The model already exists in the software you've just installed; to make changes to it, you'll first need to make a copy of the original.")}}</p>
						
			<ol>
			<li>{{_("From the Welcome page, click \"Open, Modify, and Run an Existing Model\" or click on the Models tab in the menu bar at the top of any page.")}}
			<li>{{_("Find \"Moz Gaza Current\" in the table and click the Copy button in that row.")}}
			
			<li> {{_("Name your copy -- in this example, ours is called \"Moz Gaza Current(1)\". Click OK or hit enter. Note that the copy may take several seconds to create.")}}
			<li> {{_("Find your newly created model in the table and click the Open button in that row. This will display a network diagram where you can explore the model. Circles represent locations in the supply chain, and lines represent routes. Right click any location or route to recieve detailed information.")}}
			<li> {{_("Click the Notes tab above the network diagram to add or edit notes for this model. Notes are optional and will not affect how the model runs. In this example, a useful note may read \"Rotarix vaccine introduction.\" Click Save Notes when finished.")}}</li>
			</ol>

			<h3>{{_("Adding a Vaccine to the New Model")}}</h3>
			
			<p>{{_("Now that you have a new copy of the Gaza Province, Mozambique model created, you can add Rotarix to see the impact of adding this vaccine to the current schedule. This will allow you to experience interacting with the HERMES Vaccine database, which is populated with the current WHO PQS vaccines and defining a demand schedule for the new vaccine.")}}"</p>
			  
			<ol>
				<li> {{_("With the model still open, select \"Add or remove model components\" from the options on the left side of the page. This leads to the \"Edit Components\" page, where you can add, remove, or edit components in your model, which include vaccines, transport and storage equipment, catchment populations, staff, and per diem policies.")}}
				<li>{{_("From the buttons on the left, select Vaccines if it is not already selected. This is a screen that will allow you to add any number of predefined vaccines to your newly created model, or in fact define your own.")}}</li>  
				<li>{{_("Items in the currently open model appear in the box on the left, and items available to add to this model appear in the Source box on the right. Available sources include the HERMES Database as well as other models in your database. Select HERMES Database as the source, which includes WHO prequalified items where available, as well as examples of commonly used items.")}}</li>
				<li> {{_("The HERMES Database lists WHO prequalified vaccines by antigen, followed by manufacturer and primary container size (doses per vial). For this exercise, you will introduce a Rotavirus vaccine manufactured by GlaxoSmithKline in a single-dose presentation, listed under the abbreviation \"RV GSK 1 Dose\". Scroll down to find vaccines with this name")}}</li>
				<li>{{_("Scroll down to RV and click the \"+\" next to it to display all of the Rotavirus vaccines in the database. Vaccines that are already in the current model will have their box checked in the second column, and as you can see, there are no Rotavirus vaccines currently in the model.")}}  
				<li>{{_("Multiple entries with this abbreviation exist in the database -- in this case, each differs based on the packaging (for example, whether the vaccine arrives in tubes or vials, and how many tubes or vials are packaged in each box). Click the Info button to view more details for each presentation. We will add the presentation packaged as 50 plastic tubes per carton, with a packed volume of 17.1cc per dose.")}}
				<li>{{_("Click on the appropriate vaccine to select it, and click on the arrow button to copy the vaccine from the database to the current model. The vaccine should now appear in the table on the left, along with the other vaccines in the model.")}}
				<li>{{_("This vaccine is now added to your new model. Click the Done button to return to the page for your model, and you can proceed to define the dosage schedule for the new vaccine.")}}
			</ol>
			
			<h3>{{_("Defining Demand for the Rotarix Vaccine")}}</h3> 
			<p>{{_("After adding the Rotarix vaccine to our model, you will define which populations will receive the vaccine, and how many doses they will receive during the simulation. HERMES can handle any number of vaccines and any dosage schedule a country might use. This is necessary for the model to get an accurate estimate of the number of doses that will be delivered throughout the simulation.")}}</p>
			
			<ol>
				<li>{{_("Select \"Modify the Vaccine Dose Schedule\" from the options on the left side of the page. This will display a screen showing the current dose schedule for a model.")}}
				<li>{{_("The \"Include in the dose table?\" box on the left side of the page displays components in the model that can be included in the vaccine dose schedule. You can toggle between displaying available vaccines and population types, where you may select or unselect any components to add or remove them from the schedule. Ensure the new rotavirus vaccine is selected.")}}
				<li>{{_("In the table to the right, selected vaccines appear as rows and selected population types appear as columns. You may click a cell to enter the number of doses of the vaccine in that row which will be scheduled for each member of the population type in that column over the course of one simulation. Click in the cell under the 1-11months column in the row for the rotavirus vaccine and enter 3.")}}
				<li>{{_("The new dosage schedule is now complete. Click the Done button, and you are ready to run the newly modified model.")}}
			</ol>
			
			<h3>{{_("Running the Model")}}</h3>
			<p>{{_("Now that the new vaccine has been added to the schedule, you will run a HERMES simulation to assess the impact of its addition.")}}</p>
			<ol>
			<li>{{_("Select \"Run a Simulation Experiment with this Model\" from the options on the left side of the page. A new screen will open with options for running the model.")}}
			<li>{{_("Type a name for this set of runs and specify the number of times you wish to run the model when generating this set of results. In addition to results from individual runs, an average will be reported for each set of results. For this exercise, 1 run will suffice.")}}
			<li>{{_("Run parameters can also be adjusted on this page. The default settings do not need to be changed for this exercise.")}}
			<li>{{_("Click the Submit button to begin the model validation process. A table will popup to display any errors the validator found. \"Fatal Errors\" will likely cause the run to fail before the simulation is complete, thus returning no results. \"Warnings\" indicate items that may be erroneous but would most likely not cause the run to fail.")}}
			<li>{{_("Click the Run Simulation button to continue. This leads to the Run Status page, which displays the progress of all runs begun during the current session. The Status column will update periodically until the run finishes. Depending on how powerful your computer is, this could take several minutes (up to 15) so please be patient -- it is currently running a very sophisticated simulation of the supply chain of the province of Gaza.")}}
			</ol>

			<h3>{{_("Viewing Results")}}</h3>
			<p>{{_("Once the run has completed, the results of the simulation are ready to explore.")}}</p>
			<ol>
			<li>{{_("In the menu bar at the top of the page, click on the Results tab. Available results are grouped by model on the left.")}}
			<li>{{_("Click on the name of the model you ran to expand the list of results for that model. Click on \"Average Result\" for the set of results you generated.")}}
			<li>{{_("Explore the results on this page and in the Geographic Visualization, Network Visualization, and downloadble Results Spreadsheet. Detailed information on the types of results shown and how to use the interactive displays can be found by clicking the \"?\" icon in the top-right corner of each page.")}}
			<li>{{_("Multiple results can be open at the same time and will display in tabs on the same page. Feel free to run the original Gaza Province model without adding any new vaccines, and compare the results to the ones you generated here. The results should show that Rotarix introduction leads to lower vaccine availability with higher storage and transport utilization.")}}
			</ol>
			
			<h2>{{_("Exercise 2: Create and Modify a New Model with Costing")}}</h2>
			<p>{{_("You have completed the HERMES Vaccine Introduction Tutorial Exercise. To further explore the possibilities with the HERMES software, you'll create a new model from scratch, modify it with an advanced interface, and add cost data. Because you now have some experience using the software, this exercise is more open-ended. We encourage you to explore the functionality on each page.")}}</p>
			<ol>
			<li>{{_("Click on the Create tab in the menu bar and select \"Create a New Model\" to enter the HERMES model creation guided workflow.")}} 
			<li>{{_("Follow the guided workflow to create a new model of a vaccine supply chain with any structure or characteristics you choose.")}}
			<li>{{_("Once your model is created, you will be directed to the page for that model. From the options on the left, go to the \"Advanced Model Editor\" to edit individual locations and routes. Click the \"?\" icon for more information about available actions on this page, including how to move locations, create new locations and routes, and recursively edit locations. Afterwards, click the Done button to return to the model page.")}}
			<li>{{_("From the options on the left, select \"Add and modify costs\" to add details that will allow you to view costing results once the model is run.")}}
			<li>{{_("Feel free to make another copy of the Gaza province model or your new model and modify it using the \"Advanced Model Editor\" interface to implement additional scenarios. Run the modified version and compare results across experiments.")}}
			</ol>
			 
			<p>{{_("If you have any questions or issues, please email")}} <a href="mailto:hermes-support@psc.edu">hermes-support@psc.edu</a>.  {{_("For more information about the HERMES project, visit")}} <a href="http://hermes.psc.edu">http://hermes.psc.edu</a>.</p>
		</div>
	</div>

<script>
$(function() { $(document).hrmWidget({widget:'stdDoneButton', doneURL:'{{breadcrumbPairs.getDoneURL()}}'}); });
</script>
