<p>
Specify the shipping policy at each level in the (model name) supply chain. 
Shipping policies within HERMES determine how healthcare products are distributed from higher levels to lower 
levels and depend on three parameters: the number of products shipped per trip, where the shipment originates, 
and how often the shipment occurs. 
</p>
<br>
<p>
The number of products can be fixed or variable; in fixed product shipments, a fixed number of products is always shipped, 
as long as that number of products is available at the originating location (if there are not enough products, all available are shipped). 
In variable product shipments, the amount of products is determined by the anticipated demand at the receiving location. For example, 
a health clinic that expects to administer 15 BGC vaccines within the shipping interval would receive 15 vaccines in a variable product shipment.
</p>
<br>
<p>Shipment origination can be at the supplier or at the receiver. Shipments picked up by the receiver originate from the receiving location; 
shipments dropped off by the supplier originate from the supplying location. Resources such as vehicles and labor are used by the originating location. 
For example, a shipment being dropped off by a national store at a regional store would use a driver and vehicle that originated at the national store.
</p>
<br>
<p>
Frequency of shipments can be fixed or as-needed. Fixed shipments happen at regular time intervals, 
while as-needed shipments happen when the receiving location's stock falls below a certain threshold. 
Here users can specify this threshold as a percentage of total storage space at the receiving location.
</p>
<br>
<p>
HERMES Create-a-model assigns the same shipping policies to all routes between adjacent levels.
All of these settings can me modified after the basic model structure is created via the <b>Make Adjustments</b> Page or 
in even further detail via the HERMES Edit-a-model workflow.
</p>
