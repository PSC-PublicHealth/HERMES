<p>{{_("Make advanced modifications to a model using the Advanced Model Editor")}}.
{{_('Click the "+" next to any location to view the routes and locations directly below it. Use the "edit" buttons and select "Edit Store" or "Edit Route" to edit any individual location or route. Select from among the store and route viewing options to view, edit, and hide information across multiple locations.')}}
</p>
<br><br>
<p>
{{_("Moving locations in the network")}}:
</p>
<br>
<p>
{{_("Click and drag a location to change its position in the network. To change the supplier of a location, drag the location onto the desired supplier name and release. Any recipients will continue to be supplied by that location after it is moved.")}}
</p>
<br>
<p>
{{_("To add a location to an existing route, drag the location onto the desired route name and release. This will add the location to any other location(s) already on that route, thus converting a point-to-point route into a delivery loop. Drag locations within a route to change the order they are supplied in the delivery loop.")}}
</p>
<br>
<p>
{{_('To remove a location from the network, click "edit" and select "Delete Store."')}}
</p>
<br><br>
<p>
{{_('Unattached locations')}}:
</p>
<br>
<p>
{{_('To temporarily remove a location from the network, drag it onto the space labeled "Unattached" on the right. This can also be achieved by clicking the "edit" button next to a location and selecting "Detach Store." Some changes to the network will automatically result in locations becoming unattached. Unattached locations are removed from the supply chain network and must be added again (by clicking and dragging to the desired location) if they are to remain in the model.')}}
</p>
<br><br>
<p>
{{_("Adding new locations and routes")}}:
</p>
<br>
<p>
{{_('To add a new location, find a similar location in the network, click the "edit" button next to that store, and select "Copy Store to Unattached." A copy of that store will then appear in the "Unattached" section. Edit the copy as needed, and drag the unattached location to its new position in the network')}}.
</p>
<br>
<p>
{{_('Actions such as adding a new location will automatically create a new route between that location and its supplier. Before generating new routes, one existing route can be specified as a template for newly created routes to copy. If a template is specified, new routes will be assigned the same shipping policies, vehicle type, and per diem policy as the template route. To set a route as the default template, click the "edit" button next to the route and select "set as default template." This setting can be changed by setting a different route as the default or by clicking "Clear" next to the currently selected route displayed above the supply chain network.')}}
</p>
<br><br>
<p>
{{_('Recursive editing')}}:
</p>
<br>
<p>
{{_('Locations can be modified individually or recursively. Recursive edits apply to all locations at a specified level below a selected location in the network. Click "edit" next to a location and select "Recursive Edit." In the dialog that appears, select the level of stores which will be edited, and the field that will be edited.')}}
</p>
<br>
<p>
{{_('For example, to add one fridge to each District store in one Region, the affected Region would be selected for a recursive edit. The District level and the storage field would be selected. Among the new options that would appear, the action "Add" would be selected, a count of 1 would be specified to indicate 1 new fridge per location, and the type of fridge would be selected.')}} 
</p>
<p>
{{_("Validation")}}:
</p>
<br><br>
<p>
{{_('To check the completeness of information in a model, select "Model Validation" and "Validate Model." The validator will list issues under the relevant locations and routes.')}}
</p>