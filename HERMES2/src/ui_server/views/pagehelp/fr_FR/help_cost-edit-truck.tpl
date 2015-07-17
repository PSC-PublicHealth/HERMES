<h3>{{_("The Vehicle Costs Table</h3>
		{{_("This table allows you to set or adjust costing information associated with transport vehicles.
<ul>
<li>{{_("If the model you want does not appear in the Showing Costs for selector, it may be because results have already been calculated for the model and changing the model would invalidate those results.  Only models that can be safely changed show in the selector.  You may need to make a fresh copy of your model, or go to the Results screen and delete the model's results.")}}

<li>{{_("The Base Cost represents the initial purchase price of the vehicle, with Currency and Base Cost Year specifying the currency (e.g. USD for U.S. Dollars) and year of the purchase.")}}
<li>{{_("Km To Amortize gives the total travel distance at which the vehicle is expected to require replacement.  The base cost is amortized over the time it takes the vehicle to accumulate this travel distance.")}}
<li>{{_("Fuel Consumption gives the rate at which fuel is consumed, e.g. km per liter.  This number is used with the fuel costs specified on the Fuel And Power Costs page to compute total fuel costs for the vehicle.  If you wish to change the fuel type for a vehicle, you must do so with the general type editor for vehicles.")}}
<li>{{_("For 'Fixed Fare' costs, the cost of a single fare is given in the 'Fuel Consumption' field.  The currency and year are given in the Currency and Base Cost Year columns.  Typically the Base Cost will be zero in this case, since the transit vehicle is presumably not owned by the vaccination system.")}}

</ul>