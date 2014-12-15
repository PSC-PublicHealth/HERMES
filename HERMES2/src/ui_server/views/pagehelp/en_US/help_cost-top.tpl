<h3>Setting Up Cost Calculations</h3>
This page is the starting point for preparing your model to produce detailed cost estimates.  If you ask a model to produce cost
estimates when it does not have all the information needed to do so, the run will fail.
<ul>

<li>If the model you want does not appear in the <b>Showing Costs for</b> selector, it may be because results have already been
calculated for the model and changing the model would invalidate those results.  Only models that can be safely changed show
in the selector.  You may need to make a fresh copy of your model, or go to the <em>Results</em> screen and delete the model's
results.

<li>You can use the <b>Check Completeness</b> button to produce a list of missing model information, if any.

<li>Un-checking the <b>Enable microcosting for this model?</b> checkbox 
will turn off cost calculations for your model so that it can be run with incomplete cost information.

<li><b>Base Currency</b> and <b>Base Year</b> specify the currency and year in which all costing output will be represented.  Any
costs or prices in other currencies or years will be converted to the given year as HERMES runs.

<li><b>Inflation Rate</b> is just the year-over-year rate of inflation for your model.  When HERMES converts costs with different
base years, this inflation rate is used.

<li><b>Storage Maintenance</b> gives the maintenance cost for each item of storage (refrigerators, for example) as a percentage of
initial purchase cost of the item.  The same value applies to solar panels.

<li><b>Vehicle Maintenance</b> gives the maintenance cost for each vehicle as a percentage of its fuel cost.  For example, 
in a cost calculation where a given truck burned 100 liters of gasoline at 2 USD per liter, the total fuel cost for the truck
would be 200 USD and a maintenance percentage of 5% would indicate an additional 10 USD for vehicle maintenance.

<li>The <b>Fuel and Power</b> button leads to a screen where you can specify the in-country costs of various forms of fuel 
and power.

<li>The other <b>Cost Components</b> buttons lead to screens where costs associated with specific aspects of the model can
be specified.  As each section is completed its label will change from 'Begin' to 'Continue', and then finally to 'Revisit'
when all necessary information has been specified.
</ul>