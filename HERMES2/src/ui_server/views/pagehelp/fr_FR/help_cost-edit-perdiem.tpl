<h3>{{_("Setting Per Diem Costs")}}</h3>
{{_("This page provides two tables.  The first allows you to set the details of each per diem policy in your model.  The second allows you to set the per diem policy associated with each route in the model.")}}
<ul>
<li>{{_("If the model you want does not appear in the Showing Costs for selector, it may be because results have already been calculated for the model and changing the model would invalidate those results.  Only models that can be safely changed show in the selector.  You may need to make a fresh copy of your model, or go to the Results screen and delete the model's results.")}}
<li>{{_("For a given per diem policy, the driver will be paid a per diem of the given Base Amount, specified in the given Currency at the given Base Amount Year, if certain policy-specific rules are satisfied.  The other fields on the per diem policy line specify those other rules.")}}
<li>{{_("If Must Be Overnight? is true (checked), no per diems will be paid for trips which end on the same day they began.")}}
<li>{{_("If Count First Day? is true (checked), a per diem is paid for the first day of the trip.  For example, if a driver starts a route on Tuesday and returns on the following Thursday, the driver would be entitled to three per diems (assuming all other rules are satisfied).  If 'Count First Day?' was not true, the driver would be entitled to only two per diems.")}}
<li>{{_("Min Km Home gives a minimum number of kilometers from the truck's home base that the truck must be to to receive a per diem on any given day.  A multi-day trip for which only some days are spent outside this range will pay per diems only on that subset of days.")}}
<li>{{_("The Route Per Diem Rules table allows you to set the per diem rule for any given route in the model.  (This may also be done from the Models/Modify page, which provides some recursive setting tools).  In this table, routes are organized by the model level of the route's supplier warehouse.")}}
<li>{{_("To access an individual route in this table, unfold the appropriate group by clicking on the '+' icon to the left of the level name.")}}

</ul>