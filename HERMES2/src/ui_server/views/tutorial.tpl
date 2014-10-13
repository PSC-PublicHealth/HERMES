%rebase outer_wrapper _=_,title_slogan=_('HERMES Graphical User Inferface Start'),inlizer=inlizer

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
			<p> {{_("HERMES is a software platform that allows users to generate a detailed discrete event simulation modelo of any healthcare supply chain. This simulation model can serve as a \"virtual laboratory\" for decision makers (e.g., policy makers, health officials, funders, investors, vaccine and other technology developers, manufacturers, distributors, logisticians, scientists, and researchers) to address a variety of important questions.")}}</p>

			<p>{{_("HERMES simulates a given supply chain's locations and equipment, transport routes, the employees who staff these locations and transport routes, and the patients who receive the healthcare product in question. To do this, the user inputs information or selects from a variety of pre-programmed options. The resulting models can answer a variety of questions, displaying results in many different graphical and tabular formats.")}}
			</p>

			<p>{{_("The following is a brief exercise to get you familiar with the the HERMES User Interface and perform a simple experiment on a already established model")}}</p>
			
			<p><h2>{{_("Exercise: Modify an Existing Model  (Addition of Rotarix vaccine) ")}}</h2></p>

			<h3>{{_("Making a Copy of the Gaza Province, Mozambique Model")}}</h3>
			
			<p>{{_("To start using HERMES, you'll be modifying an existing model of the vaccine supply chain in . The file already exists in the appliance you've just installed; to make changes to it, you'll first need to make a copy of the original.")}}"</p>
						
			<ol>
			<li>{{_("From the home page, click the Models tab.")}}
			<li>{{_("Click the Copy button on the left side of your screen, then make sure \"Gaza Current\" is selected in the Model to <b>Copy</b> dropdown that appears.")}}
			
			<li> {{_("Name your copy - in this example, ours is called \"Gaza Current Copy\". Click \"OK\" or hit enter. Note that the copy may take several seconds to create.")}}
			<li> {{_("Click the Show Button, and from the dialog, select your newly created model.  This will display a network diagram of the model.  The circles represent locations in the supply chain.  Right click on them to recieve detailed information about the location.  When you are finished exploring the model, click the Models tab to return to the list of models.")}}</li>
			</ol>

			<h2>{{_("Adding a Vaccine to the new Model")}}</h2>
			
			<p>{{_("Now that you have a new copy of the Gaza Province, Mozambique model created, you can add the Rotarix Vaccine to it so that we can see the impact of adding this vaccine to the current schedule.  This will allow you to experience interacting with the HERMES Vaccine database, which is populated with the current WHO PQS vaccines and defining a demand schedule for the new vaccine.")}}"</p>
			  
			<ol>
				<li>{{_("At the top menu bar, click on the tab labeled \"Vaccines\".  This is a screen that will allow you to add any number of predefined vaccines to your newly created model, or in fact define your own.")}}</li>  
				<li>{{_("From the dropdown menu at the top labeled \"Showing vaccine types for\", select your newly copied model (Gaza Current Copy).")}}</li>
				<li> {{_("The vaccines in the database are categorized by type, and currently showing the standard abbreviation for each type.   Feel free to explore them at your leisure.  For our purposes, we will be introducing a new Rotavirus vaccine, which has the abbreviation \"RV\".")}}</li>
				<li>{{_("Scroll down to RV and click the \"+\" next to it to display all of the Rotavirus vaccines in the database.  Vaccines that are already in the current model will have their box checked in the second column, and as you can see, there are no Rotavirus vaccines currently in the model.")}}  
				<li>{{_("Find the column labeled \"Rotavirus_GSK_50Tube_1Dose\", which is the presentation of Rotarix that we would like to add to the model.  Click on the check box to add this vaccine to the model.")}}
				<li>{{_("If you would like to see a set of characteristics for the vaccine, click on the \"Info\" button, which will show you that the \"Packed vol/dose (cc) of vaccine\" is 17.1 cc's.")}}
				<li>{{_("This vaccine is now added to your new model, we can proceed to defining the dosage schedule for the new vaccine.")}}
			</ol>
			
			<h2>{{_("Defining Vaccine Demand for the Rotarix vaccine")}}</h2> 
			<p>{{_("Now that we added the Rotarix vaccine to our model, we have to define which populations will receive the vaccine, and how many doses they will receive in a year.  HERMES can handle any number of vaccines and dosage schedule a country might use.  This is necessary for the model to get an accurate estimate of the number of doses that will be delivered throughout the simulation.")}}</p>
			
			<ol>
				<li>{{_("At the top menu bar, click on the tab labeled \"Demand\".  This will open a screen that will present the current dose schedule for a model.  There are two tables.  The one on the left shows all of the vaccines that have been included in the model.  The one on the right shows on each column heading the population type that receives vaccines in schedule.  For each row, the number of doses for each vaccine per population type is given, defining the dosage schedule for the model's program.")}}
				<li>{{_("From the dropdown menu at the top of the table on the right, select your newly copied model (Gaza Current Copy).")}}
				<li>{{_("In the left table, the check box next to \"Rotavirus_GSK_50Tube_1Dose\" should be unchecked, check it to add the vaccine to the dosage schedule.  The table on the right should refresh showing the new vaccine with zeros in all of the columns.")}}
				<li>{{_("Two doses of Rotarix is given to children under one year of age for Gaza Province, Mozambique, so in order to specify this, click on the box in the new row under the column \"0-11 months\" and put a 2 in there and hit return.")}}
				<li>{{_("Now the new dosage schedule is complete, and we are ready to run the new model.")}}
			</ol>
			
			<h2>{{_("Running the Model")}}</h2>
			<p>{{_("Now that we have added the new vaccine to the schedule, we will need to run a HERMES simulation to estimate the impact of its addition.")}}</p>
			<li>{{_("At the top menu bar, click on the tab labeled \"Run HERMES\".  A new screen will open that has a table that is currently empty.  This is the page where one can run a simulation and see its progress as it is running.")}}
			<li>{{_("Click on the button \"Run HERMES\", and this will begin a sequence of screens that will define the HERMES simulation run.")}}
			<li>{{_("On the first screen, entitled \"Beginning a Hermes Run\", choose your new model from the dropdown menu next to \"Which model do you wish to run?\".  Then in the dialogue box immediately below, give the run a unique name (e.g. Gaza Province, Mozambique with Rotarix).   Click \"Next\".")}}
			<li>{{_("The next page, entitled \"Provide Some Details\" allows you to define a few parameters that are specific to this simulation.  For now the default parameters will suffice.  Optionally, you can click on the \"Edit Parameters?\" button, and a page will come up that shows you some of the run options that HERMES has available.  Feel free to click Next to move on with the default options.")}}
			<li>{{_("The next page is a placeholder that will eventually have a display of the newly created run, this is still under development, please click the \"Start\" button.  A warning will come up that instructs you not to turn off your machine during the run.  Click \"Ok\".")}}
			<li>{{_("You will now be taken back out to the \"Run Status\" page, and you should see your new run appearing as a column.  The \"Status\" column will keep you updated as to the progress of the simulation, and it will indicate when it is finished.  Depending on how powerful your computer is this could take several minutes (up to 15), so please be patient, it is currently running a very sophisticated simulation of the supply chain of the province of Gaza.")}}

			<h2>{{_("Viewing Results")}}</h2>
			<p>{{_("Once the run has completed, the results of the simulation will be ready to explore.  Your instance of HERMES has been prepopulated with a run of the Gaza Province, Mozambique model with the EPI vaccine schedule, so we will be able to compare the simulated immunization program before and after introduction of Rotarix.")}}</p>
			<li>{{_("At the top menu bar, click on the tab \"Results\".  You now be presented with table of \"Available Results\" grouped by model and by run.")}}
			<li>{{_("To view the results without Rotarix, click the plus sign next \"Result: Gaza Current PAV Baseline\".  This was a simulation that was run twice and average results were collected over those two runs, so you should see two individual runs, and one \"Group Average\" run.")}}
			<li>{{_("Click on the row for \"Group Average\" and then click the \"Open\" button to the left.  You will be presented with a screen that at the top, gives you statistics of the simulation results by vaccine.  The one to note is the \"Vaccine Availability\" which is essentially the percentage of the demand met by the supply chain over the simulated period.  For the Baseline  each vaccine should range between 88 and 95%, which is indicating the supply chain is performing well.  Feel free to explore the visualizations using Geographic Visualization and the Fireworks diagram, although be warned that they are still under development and can take a significant amount of time to populate.")}}
			<li>{{_("Now click on the \"Results\" tab again and select the run under Gaza Province, Mozambique with Rotarix, and click the \"Open Button\".")}}  {{_("You should see that the Vaccine availability has now gone down by about 10 indicating the effect that introducing the new vaccine has on the system.")}}
	
			<p>{{_("This completes the HERMES Vaccine Introduction. To further explore the possibilities with the HERMES software, feel free to make another copy of the Gaza Province, Mozambique model and \"Modify\" it through our \"Model Editor\" interface, which gives you access to all aspects of a HERMES model, or create a new model from scratch by selecting the \"Create\" button on the Models page.")}}</P>
			 
			 
			<p>{{_("If you have any questions or issues, please email")}} <a href="mailto:hermes-support@psc.edu">hermes-support@psc.edu</a>.  {{_("For more information about the HERMES project, visit")}} <a href="http://hermes.psc.edu">http://hermes.psc.edu</a>.</p>
		</div>
	</div>
