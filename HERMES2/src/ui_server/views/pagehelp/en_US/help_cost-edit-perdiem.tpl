<h3>Setting Per Diem Costs</h3>
This page provides two tables.  The first allows you to set the details of each per diem policy in your model.  The second
allows you to set the per diem policy associated with each route in the model.
<ul>
<li>If the model you want does not appear in the <b>Showing Costs for</b> selector, it may be because results have already been
calculated for the model and changing the model would invalidate those results.  Only models that can be safely changed show
in the selector.  You may need to make a fresh copy of your model, or go to the <em>Results</em> screen and delete the model's
results.
<li>For a given per diem policy, the driver will be paid a per diem of the given <b>Base Amount</b>, specified in the given
<b>Currency</b> at the given <b>Base Amount Year</b>, if certain policy-specific rules are satisfied.  The other fields on
the per diem policy line specify those other rules.
<li>If <b>Must Be Overnight?</b> is true (checked), no per diems will be paid for trips which end on the same day they began.
<li>If <b>Count First Day?</b> is true (checked), a per diem is paid for the first day of the trip.  For example, if a driver
starts a route on Tuesday and returns on the following Thursday, the driver would be entitled to three per diems (assuming all
other rules are satisfied).  If 'Count First Day?' was not true, the driver would be entitled to only two per diems.
<li><b>Min Km Home</b> gives a minimum number of kilometers from the truck's home base that the truck must be to to receive a
per diem on any given day.  A multi-day trip for which only some days are spent outside this range will pay per diems only on
that subset of days.
<li>The <b>Route Per Diem Rules</b> table allows you to set the per diem rule for any given route in the model.  (This may also 
be done from the <em>Models/Modify</em> page, which provides some recursive setting tools).  In this table, routes are
organized by the model level of the route's supplier warehouse.
<li>To access an individual route in this table, unfold the appropriate group by clicking on the '+' icon to the left of 
the level name.

</ul>