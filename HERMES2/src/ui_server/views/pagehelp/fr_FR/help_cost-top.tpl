<h3>{{_("Setting Up Cost Calculations")}}</h3>
		{{_("This page is the starting point for preparing your model to produce detailed cost estimates.  If you ask a model to produce cost estimates when it does not have all the information needed to do so, the run will fail.
<ul>

<li>{{_("If the model you want does not appear in the Showing Costs for selector, it may be because results have already been calculated for the model and changing the model would invalidate those results.  Only models that can be safely changed show in the selector.  You may need to make a fresh copy of your model, or go to the Results screen and delete the model's results.")}}

<li>{{_("You can use the Check Completeness button to produce a list of missing model information, if any.")}}

<li>{{_("Un-checking the Enable microcosting for this model? checkbox  will turn off cost calculations for your model so that it can be run with incomplete cost information.")}}

<li>{{_("Base Currency and Base Year specify the currency and year in which all costing output will be represented.  Any costs or prices in other currencies or years will be converted to the given year as HERMES runs.")}}

<li>{{_("Inflation Rate is just the year-over-year rate of inflation for your model.  When HERMES converts costs with different base years, this inflation rate is used.")}}

<li>{{_("Storage Maintenance gives the maintenance cost for each item of storage (refrigerators, for example) as a percentage of initial purchase cost of the item.  The same value applies to solar panels.")}}

<li>{{_("Vehicle Maintenance gives the maintenance cost for each vehicle as a percentage of its fuel cost.  For example,  in a cost calculation where a given truck burned 100 liters of gasoline at 2 USD per liter, the total fuel cost for the truck would be 200 USD and a maintenance percentage of 5% would indicate an additional 10 USD for vehicle maintenance.")}}

<li>{{_("The Fuel and Power button leads to a screen where you can specify the in-country costs of various forms of fuel  and power.")}}

<li>{{_("The other Cost Components buttons lead to screens where costs associated with specific aspects of the model can be specified.  As each section is completed its label will change from 'Begin' to 'Continue', and then finally to 'Revisit' when all necessary information has been specified.")}}

<li>{{_("Vaccine purchase costs are normally excluded from cost calculations, but they can be included by selecting the  Calculate vaccine costs? checkbox.  If this option is set, the model will need to have complete costing information for its vaccines.")}}
</ul>