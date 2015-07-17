<p>{{_('View, compare, and interact with simulation results. Available results are grouped by model to the left. Click any model name to view results associated with that model. Each set of results includes the individual run instances (labeled "Run:0", "Run:1", etc.) as well as the average of that set ("Average Result"). Results from multiple experiments open in new tabs on the same page for ease of comparison. Use the "delete" button to permanently delete any individual run, average result, or set of results.')}
</p>
<br>
<p>
{{_('The Vaccine Results table lists statistics for each vaccine in the dose schedule, as well as overall statistics for all vaccines combined.')}
</p>
<br>
<ul>
<li>{{_('Doses Demanded indicates the number of doses of each vaccine that was needed at immunizing locations in order to administer the required vaccines to all people who arrived for vaccinations.')}
<li>{{_('Doses Administered indicates the number of doses that were given to people arriving for vaccinations. This number may be lower than Doses Demanded if supply chain bottlenecks or ordering policies prevented the necessary vaccines from getting where they were needed, when they were needed.')}
<li>{{_('Availability expresses the Doses Administered as a percentage of the Doses Demanded.')}
<li>{{_('Open Vial Waste is the number of doses discarded from opened vials, as a percentage of all doses in vials that were opened. Doses must be discarded from opened vials depending on the type of vaccine (lyophilized or liquid, for example) and the immunization program policies (some programs mandate discarding all opened vials at the end of every session, while others may allow some types of opened vials to be used in future sessions).')}
</ul>
<br>
<p>
{{_('Histograms display the distribution of overall vaccine availability, maximum storage utilization, and maximum transport utilization across locations.')}
</p>
<br>
<ul>
<li>{{_('Maximum Storage Utilization indicates the maximum storage capacity needed at a location during the simulation, as a percentage of the actual capacity available at that location.
<li>{{_('Maximum Transport Utilization indicates the maximum transport capacity needed for a route during the simulation, as a percentage of the actual capacity available on that route.')}
</ul>
<br>
<p>
{{_('Microcosting Results are first displayed in a table which lists costs accrued at each supply chain level during the simulation, as well as the total for all levels. The table heading states the year and currency in which all cost results are reported.')}
</p>
<br>
<p>
{{_('An interactive Zoomable Treemap allows for quick visualization of the major cost driving categories and the relative cost of each level, location, and route. The treemap displays boxes labeled with categories of costs, with the relative size of each box representing the relative share of costs attributed to that category. Clicking any box will "zoom in" the treemap to the selected category, now further broken down into subcategories. To zoom out to the previous level of costs, click on the blue bar at the top of the treemap, which displays a label of the current category.')}
</p>
<br>
<p>
{{_('An interactive Costs Bar Chart initially displays total costs by level. Clicking any level will regenerate the bar graph to show the costs accrued at each location and route at the selected level. Clicking any location or route will display the costs by category at that location or route. Return to the previous view by clicking in any empty white space in the chart.')}
</p>
<br>
<p>
{{_('Use the buttons to view a Network Visualization of simulation results, download a Results Spreadsheet with detailed data, or -- if latitude and longitude coordinates were specified for locations in this model -- view results in a Geographic Visualization.')}
</p>