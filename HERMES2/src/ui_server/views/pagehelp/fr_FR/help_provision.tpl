<p>{{_('This step assigns quantities of equipment and population to locations by level. Rows in the table list the storage devices and population types that were added to the model in a previous step. Each supply chain level is shown as a column in the table.')}}
</p>
<br>
<p>
{{_('Click in a cell to edit the number of devices or people for a typical location at that level, and HERMES will add the specified number of that component to every location at that level. For example, entering "2" for cold rooms at a Region level would assign 2 cold rooms to each location at the Region level, regardless of how many Region locations exist.')}} 
</p>
<br>
<p>
{{_('Similarly, populations represent the people who would be vaccinated at each location in a given level. Only enter population numbers for levels that administer vaccinations. A level that solely stores and distributes vaccines should not include any populations here. For example, specifying 100 newborns for the Health Post level would assign 100 newborns to every Health Post. If locations at higher levels in this example do not administer vaccines to newborns, then they should have 0 newborns assigned here. You can later modify these for specific locations or groups of locations using the Advanced Model Editor'}}.
</p>