<p>{{_('This is the first step in running a HERMES model. Once you have finished this short set of pages, the execution of your model will begin. If you leave this sequence of screens too early, your model will not begin running but you will be able to return to the sequence where you left off by selecting Run again.')}} 
</p>
<br><br>
<p>
{{_('Entering run details')}}:
</p>
<br>
<p>
{{_('Here you will enter a name for results and specify the number of times you wish to run the model when generating this set of results. To better capture the day-to-day variation that occurs in the real world, HERMES models are stochastic (unless otherwise specified in the parameters). This means each run will generate somewhat different results. For example, daily demand at an immunizing location is not uniform -- rather, some days will see more patients than others at any given location. Thus, HERMES stochastically generates daily demand as a Poisson distribution.')}}
</p>
<br>
<p>
{{_('To obtain results that are representative of the model, taking the average of multiple runs is recommended. Each model is different, but a good rule of thumb is to use the average of 10 runs for results that will not vary significantly due to stochasticity alone.')}}
</p><br><br>
<p>
{{_('Adjusting parameters')}}:
</p>
<br>
<p>
{{_('Three basic run parameters are displayed to allow editing of the simulation length, shipments from the manufacturer, and buffer stock.')}}
</p>
<br>
<p>
{{_('The number of simulation days specifies the time period that each run will simulate. Because each simulated month in HERMES is 4 weeks long, one year is equal to 336 days.')}}
</p>
<br>
<p>
{{_('The number of shipments from the manufacturer per year indicates the annual number of times the location at the highest level receives vaccines. For example, if vaccines enter the supply chain via quarterly deliveries to the top level, then 4 would be entered here.')}}
</p>
<br>
<p>
{{_('The factor for buffer stock from the manufacturer specifies how shipments to the top level are calculated. Typically, orders are calculated based on expected vaccine demand and open vial wastage and then inflated by a factor to allow for additional buffer stock. A value of 1.25 in this field would indicate a 25% buffer stock policy, in which the location at the top level will receive 25% more vaccines than the amount expected to be necessary (if adequate storage capacity exists at that location).')}}
</p><br><br>
<p>
{{_('Validating model')}}:
</p>
<br>
<p>
{{_('Once this page is complete, clicking Submit will begin the model validation process. A table will popup to display any errors the validator found. "Fatal Errors" will likely cause the run to fail before the simulation is complete, thus returning no results. "Warnings" indicate items that may be erroneous but would most likely not cause the run to fail. However, these items may lead to erroneous results if they reflect actual errors in the model. If errors are found, you may go directly from this dialog to the Advanced Model Editor to address the issues or you may proceed with running the simulation.')}}
</p>