<p>{{_("Users may make adjustments to each of the locations and routes between locations within the <b>Make Adjustments</b> table. Whereas the previous steps generated location names, assigned shipping policies by level, and distributed locations evenly across suppliers, this step allows users to modify individually the names of each location, the shipping policies between locations, and the number of locations supplied by each location. Click in any row to select a location, and type or select from the available options to edit information for that particular location. Below is more information about each potential edit.")}}
</p>
<br>
<p>
{{_("Location Names")}}:
</p><br> 
<p>
{{_("Location and level names are text-only inputs and can be fully customized by the user -- these are used for labelling purposes only, so users should use the naming conventions most familiar and meaningful. Click the triangle to the left of a location name to expand or collapse the locations below it.")}}<br>
</p>
<br>
<p>{{_("Shipping Policies")}}:</p>
<br>
<p>
{{_("Edit the shipping policy for any route in the supply chain. ")}}
		{{_("Shipping policies within HERMES determine how healthcare products are distributed from higher levels to lower levels and depend on three parameters: the number of products shipped per trip, where the shipment originates, and how often the shipment occurs.")}}
</p>
<br>
<p>
{{_("The quantify of products can be fixed or variable; in fixed product shipments, a fixed number of products is always shipped, as long as that number of products is available at the originating location  (if there are not enough products, all available are shipped). In variable product shipments, the quantity of products is determined by the anticipated demand at the receiving location. For example, a health clinic that expects to need 15 BCG vaccine vials within the shipping interval would receive 15 BCG vials in a variable product shipment.")}}
</p>
<br>
<p>
{{_("Shipments can originate at the supplier or at the receiver. Shipments picked up by the receiver originate from the receiving location; shipments dropped off by the supplier originate from the supplying location. Resources such as vehicles and labor are used by the originating location. For example, a shipment being dropped off by a national store at a regional store would use a driver and vehicle that originated at the national store.")}}
</p>
<br>
<p> 
{{_("Frequency of shipments can be fixed or as-needed. Fixed shipments happen at regular time intervals, while as-needed shipments happen when the receiving location's stock falls below a certain threshold. Here users can specify this threshold as a percentage of total storage space at the receiving location.")}}
</p>
<br>
<p>{{_("Number of Locations Supplied by this Location")}}:</p>
<br>
<p>
{{_("For each location in the model, this column lists the number of locations it directly supplies in the level below it. Changing any value in this column will change the total number of locations in the model. For example, adding 1 location to the number supplied by a location in Level 2 will raise the total number of locations at Level 3 by 1. Similarly, reducing the number of locations supplied by a Level 2 location will reduce the total number of locations at Level 3. Locations at the lowest level of the supply chain must have no clients, because they do not supply any other locations.")}}
</p>
 

