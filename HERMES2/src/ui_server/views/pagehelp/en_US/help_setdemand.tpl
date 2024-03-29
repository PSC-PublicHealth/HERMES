<p>In HERMES, demand is determined by the populations served by each location and the vaccine schedule for each population type. Here, you will define the vaccine dose schedule for this model. 
<br><br>
<p>The <b>Include in the dose table?</b> box on the left side of the page displays components in the model that can be included in the vaccine dose schedule. You can toggle between displaying available vaccines and population types, where you may select or unselect any components to add or remove them from the schedule. 
<br><br>
<p>In the <b>dose table</b> to the right, selected vaccines appear as rows and selected population types appear as columns. You may click a cell to enter the number of doses of the vaccine in that row which will be scheduled for each member of the population type in that column over the course of one simulation. 
<p>For example, if including newborns and a BCG vaccine, a user would enter "1" to indicate that each newborn in the model would be scheduled to receive 1 dose of BCG.
<br><br><br>
<p>Select <b>Show Advanced Options?</b> to view additional information you can include about vaccine demand: 
<br><br>
<ul>
<li>The <b>proportion of population getting vaccinated</b> is the percentage of all model populations who will arrive for vaccinations in the simulation. The default value is 1, meaning 100% of the populations in the model will present for vaccines at immunization locations during each simulation run. 
<li>Entering a value into <b>projected vs. actual</b> adjusts the expected demand (the size of the population that is expected to arrive for vaccinations, which is taken into account when calculating the amount of each product to order). The expected demand will equal the actual demand, scaled by the factor entered. The default value is 1, meaning the number of people expected to arrive for vaccinations will equal 100% of the people actually arriving. 
<li>Select <b>Scale vaccines separately?</b> to specify the <b>proportion of population getting vaccinated</b> and <b>projected vs. actual</b> factors independently for each specific vaccine. 
<p>For example, to enter an 85% target coverage for one vaccine and a 90% target coverage for another, a user would edit the proportion of the population getting vaccinated column to "0.85" and "0.9" for the appropriate rows. 
<li>Select <b>Treatment Calendar</b> to select which days, weeks, and months the immunizing locations administer vaccines to all population types. 
<li>Select <b>Schedule population types separately?</b> to specify which days, weeks, and months the immunizing locations administer vaccines to each individual population type. 
</ul> 
