<h3>{{_("The Vehicle Costs Table")}}</h3>
{{_("This table allows you to set or adjust costing information associated with storage devices like refrigerators, freezers, and vaccine carriers.")}}
<ul>
<li>{{_("If the model you want does not appear in the <b>Showing Costs for</b> selector, it may be because results have already been calculated for the model and changing the model would invalidate those results.  Only models that can be safely changed show in the selector.  You may need to make a fresh copy of your model, or go to the Results screen and delete the model's results.")}}

<li>{{_("The Base Cost represents the initial purchase price of the storage device, with Currency and Base Cost Year specifying the currency (e.g. USD for U.S. Dollars) and year of the purchase.")}}
<li>{{_(Years To Amortize gives the total number of years at which the device is expected to require replacement.  The base cost is amortized over this time.")}}

<li>{{_("Ongoing costs are the costs of running the device- electricity or LP gas for example.  The Ongoing column specifies the rate at which fuel or power is used.  It is combined with fuel cost information to produce an ongoing cost figure for the device.  Note that these costs are separate from amortization costs.")}}

<li>{{_("Ongoing cost for ice and blue ice are special cases.  A cold box will require a given number of liters of ice per charge.  That number will be given in the Ongoing column.  HERMES attempts to calculate the number of times the device will be charge in the course of a simulation, and uses that number along with the number of liters per charge and the cost to freeze a liter of ice to estimate the cost of operating the cold box.")}}

<li>{{_("Solar power is another special case.  A solar refrigerator will require a certain number of kilowatts of electricity from solar panels to operate.  These panels are assumed to be purchased once and amortized.  For solar storage, the number of  kilowatts needed is given in the Ongoing column.  This is used with the cost of an installed kilowatt of solar power to estimate the amortization cost of the solar panels over the HERMES run.")}}
</ul>