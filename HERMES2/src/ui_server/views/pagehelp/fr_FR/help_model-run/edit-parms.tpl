
<h3>HERMES Input File Keywords</h3>
<p>

<table>
<tr><th align="right">Keyword<th align="center">Type<th align="center">Default<th align="left">Description</tr>
<tr><td align="right">autoupdatethresholds<td align="center">TF<td align="center">False<td align="left">Recalculate trigger thresholds for pull shipments each time a shipment occurs</tr>
<tr><td align="right">birthrate <td align="center">float<td align="center">-1.0<td align="left">The birth rate expressed in number of births per 1000 people</tr>
<tr><td align="right">burnindays<td align="center">int<td align="center">30<td align="left">Number of Days of Burning for the simulation</tr>
<tr><td align="right">calendarcycle<td align="center">int<td align="center">0<td align="left">number of days in the calendar cycle</tr>
<tr><td align="right">calendarfile<td align="center">stringOrNone<td align="center">None<td align="left">filename for specifying the calendar demand</tr>
<tr><td align="right">campaignvaccines<td align="center">string_list<td align="center">None<td align="left">List of vaccines that will be considered campaign vaccines and will use demandExpectation rather than instantaneous demand</tr>
<tr><td align="right">catchupcoverage<td align="center">float<td align="center">1.0<td align="left">proportion of the population for catchup to vaccinate</tr>
<tr><td align="right">catchupdays<td align="center">int<td align="center">0<td align="left">number of days for the catchup campaign</tr>
<tr><td align="right">catchupfile<td align="center">stringOrNone<td align="center">None<td align="left">filename for specifying the catchup demand</tr>
<tr><td align="right">catchupstart<td align="center">int<td align="center">0<td align="left">day to start the catchup campaign</tr>
<tr><td align="right">catchupvaccines<td align="center">string_list<td align="center">V_Dengue<td align="left">names of vaccines to be used in the catchup campaign</tr>
<tr><td align="right">centrallevellist<td align="center">string_list<td align="center">Central<td align="left">The central or hub CATEGORY or level that is used in this model</tr>
<tr><td align="right">cliniclevellist<td align="center">string_list<td align="center">Clinic<td align="left">The CATEGORYs or levels that can administer vaccines in this model</tr>
<tr><td align="right">consumptioncalendarfile<td align="center">stringOrNone<td align="center">None<td align="left">filename for specifying the calendar demand for consumption calculations</tr>
<tr><td align="right">consumptiondemandfile<td align="center">stringOrNone<td align="center">None<td align="left">file defining the demand for consumption quantity calculations used in the model</tr>
<tr><td align="right">currencybase<td align="center">string<td align="center">USD<td align="left">Currency code of the currency to be used for all cost calculations</tr>
<tr><td align="right">currencybaseyear<td align="center">int<td align="center">2011<td align="left">Currency conversions will be done using tabulated data for this year</tr>
<tr><td align="right">currencyconversionfile<td align="center">string<td align="center">CurrencyConversionTable.csv<td align="left">A CSV file providing currency conversion factors</tr>
<tr><td align="right">currentpopulationyear<td align="center">int<td align="center">-1<td align="left">The Year in which the current population in the Storesfile is defined for</tr>
<tr><td align="right">customoutput<td align="center">string_list<td align="center">None<td align="left">Create a custom output file based on the csv file pointed to in the argument.  There can be multiple custom outputs</tr>
<tr><td align="right">dayspermonth<td align="center">int<td align="center">28<td align="left">The number of days in a month, this is dependent on which model you are planning to run</tr>
<tr><td align="right">deathrate<td align="center">float<td align="center">-1.0<td align="left">The death rate expressed in number of deaths per 1000 people</tr>
<tr><td align="right">debug<td align="center">TF<td align="center">False<td align="left"> turns on debugging output</tr>
<tr><td align="right">defaultpullmeaninterval<td align="center">float<td align="center">30.0<td align="left">What should be the planned time between shipments on implied pull links?  These do not appear in the Routes file</tr>
<tr><td align="right">defaultshipstartuplatency<td align="center">floatOrNone<td align="center">None<td align="left">If the model respects this value it provides StartupLatencyDays information for routes with no corresponding entry</tr>
<tr><td align="right">defaulttruckinterval<td align="center">float<td align="center">0.0<td align="left">What is the minimum time between shipments on implied pull links?  These do not appear in the Routes file</tr>
<tr><td align="right">defaulttrucktypename<td align="center">string<td align="center">default<td align="left">What type of truck should be used for implied pull links?  These do not appear in the Routes file</tr>
<tr><td align="right">deliverydelayfrequency<td align="center">floatOrNone<td align="center">None<td align="left">frequency of shipping delay incurred during transport (0.0-1.0)</tr>
<tr><td align="right">deliverydelaymagnitude<td align="center">floatOrNone<td align="center">None<td align="left">magnitude in days of shipping delays</tr>
<tr><td align="right">deliverydelaysigma<td align="center">floatOrNone<td align="center">None<td align="left">if this value exists use a normal distribution for the delay with this value as the standard deviation</tr>
<tr><td align="right">demandfile<td align="center">stringOrNone<td align="center">None<td align="left">file defining the demand for the model. </tr>
<tr><td align="right">discardunusedvaccine<td align="center">TF<td align="center">False<td align="left">If true the clinic will discard any remaining supply of vaccine at the end of a treatment session</tr>
<tr><td align="right">eventlog<td align="center">stringOrNone<td align="center">None<td align="left">File into which event logging records should be written</tr>
<tr><td align="right">eventloglist<td align="center">string_list<td align="center">None<td align="left">List of events to record in the log (empty list means all of them)</tr>
<tr><td align="right">eventlogregex<td align="center">stringOrNone<td align="center">None<td align="left">A regular expression (regex) to be used to filter out unwanted event log entries</tr>
<tr><td align="right">factoryoverstockscale<td align="center">float<td align="center">1.0<td align="left">Scale the anticipated demand by this factor to determine factory production</tr>
<tr><td align="right">factoryshipmentsperyear<td align="center">float<td align="center">4.0<td align="left">The factory will ship this many times per year at equal intervals</tr>
<tr><td align="right">factorystartuplatency<td align="center">float<td align="center">0.0<td align="left">Time in days after 0.0 that the factory makes its first delivery and begins its cycle</tr>
<tr><td align="right">fridgefile<td align="center">stringOrNone<td align="center">None<td align="left">file to define or override the unified fridge type definitions</tr>
<tr><td align="right">gapstorefile<td align="center">stringOrNone<td align="center">None<td align="left">file defining the storage devices by level that will be used to fill existing storage gaps, Only needed if doing gap analysis – then Defaults to None id illegal value making this input required, then Defaults to None is illegal value making this input required</tr>
<tr><td align="right">googleearthviz<td align="center">TF<td align="center">False<td align="left">Defines whether you want to create a set of Google Earth Vizualizations</tr>
<tr><td align="right">googleearthvizcolumnheight<td align="center">int<td align="center">100000<td align="left">Height of the columns that will be displayed on Google Earth, I think these are in miles, but I am not sure.</tr>
<tr><td align="right">googleearthvizinitday<td align="center">int<td align="center">1<td align="left"></tr>
<tr><td align="right">googleearthvizinitmonth<td align="center">int<td align="center">1<td align="left"></tr>
<tr><td align="right">googleearthvizinityear<td align="center">int<td align="center">2012<td align="left"></tr>
<tr><td align="right">googleearthviznumberofcolors<td align="center">int<td align="center">100<td align="left">Number of colors between red and blue to display on Google earth</tr>
<tr><td align="right">googleearthvizsegments<td align="center">int<td align="center">1<td align="left">For large simulations, this defines how many segments you would like to create in time so that everything shows up on GE</tr>
<tr><td align="right">googleearthviztitle<td align="center">stringOrNone<td align="center">['None', 'Title of the Google Earth Vizualization', '']<td align="left"></tr>
<tr><td align="right">icefile<td align="center">stringOrNone<td align="center">None<td align="left">file to define or override the unified ice type definitions</tr>
<tr><td align="right">includecatchup<td align="center">TF<td align="center">False<td align="left">adds a catchup campaign to the demandmodel</tr>
<tr><td align="right">infantmortality<td align="center">float<td align="center">-1.0<td align="left">The infant mortality rate expressed in number of deaths per 1000 births</tr>
<tr><td align="right">initialovw<td align="center">stringOrNone<td align="center">None<td align="left">filename for input csv file containing initial OVW values</tr>
<tr><td align="right">levellist<td align="center">string_list<td align="center">['Central', 'Region', 'District', 'Clinic']<td align="left">The CATEGORYs or levels that may be used in this model</tr>
<tr><td align="right">mergefridgeyears<td align="center">TF<td align="center">True<td align="left">if set fridges the name of which includes a specific year field are replaced with their _U_-year equivalent if that type has the same storage characteristics.  This is done just to reduce the number of fridge types tracked</tr>
<tr><td align="right">minion<td align="center">TF<td align="center">False<td align="left">Behave as for a minion process.  For example format stderr output for machine processing.</tr>
<tr><td align="right">model<td align="center">string<td align="center">model_default<td align="left">model to be run: e.g. 'model_niger'</tr>
<tr><td align="right">monitor<td align="center">string_list<td align="center">None<td align="left">monitor this list of warehouses</tr>
<tr><td align="right">monthlyreports<td align="center">TF<td align="center">False<td align="left">turns on monthly reporting</tr>
<tr><td align="right">monvax<td align="center">string_list<td align="center">None<td align="left">when monitoring watch this vaccine ('all' for all)</tr>
<tr><td align="right">outputfile<td align="center">stringOrNone<td align="center">None<td align="left">filename for output text - default is stdout</tr>
<tr><td align="right">packagefile<td align="center">stringOrNone<td align="center">None<td align="left">file to define or override the unified packaging type definitions</tr>
<tr><td align="right">peoplefile<td align="center">stringOrNone<td align="center">None<td align="left">file to define or override the unified people type definitions</tr>
<tr><td align="right">pickupdelayfrequency<td align="center">floatOrNone<td align="center">None<td align="left">frequency of shipping delay incurred before transport starts (0.0-1.0)</tr>
<tr><td align="right">pickupdelaymagnitude<td align="center">floatOrNone<td align="center">None<td align="left">magnitude in days of shipping delays</tr>
<tr><td align="right">pickupdelayreorder<td align="center">TF<td align="center">False<td align="left">if set we recalculate the order on a pull shipment</tr>
<tr><td align="right">pickupdelaysigma<td align="center">floatOrNone<td align="center">None<td align="left">if this value exists use a normal distribution for the delay with this value as the standard deviation</tr>
<tr><td align="right">poweroutageaffectedratio<td align="center">floatOrNone<td align="center">None<td align="left"> if exists percent chance of a warehouse to be affected within its cluster</tr>
<tr><td align="right">poweroutageclusterid<td align="center">stringOrNone<td align="center">None<td align="left"> if exists sets a default clusterid for unlabeled poweroutage records</tr>
<tr><td align="right">poweroutagedurationdays<td align="center">floatOrNone<td align="center">None<td align="left"> duration of power outages</tr>
<tr><td align="right">poweroutagedurationsigma<td align="center">floatOrNone<td align="center">None<td align="left"> if exists use normal distribution for power outage duration with this value as the standard deviation</tr>
<tr><td align="right">poweroutagefrequencyperyear<td align="center">floatOrNone<td align="center">None<td align="left"> frequency of power outages per cluster per year</tr>
<tr><td align="right">pricetable<td align="center">stringOrNone<td align="center">None<td align="left">A CSV file containing costing information for items used in this simulation – 'None' implies no costing analysis</tr>
<tr><td align="right">pvsdbugfix<td align="center">TF<td align="center">False<td align="left">if true employ the Joels PVSD bug fix</tr>
<tr><td align="right">routesfile<td align="center">string<td align="center">None<td align="left">file defining the routes table for the model. Default of None is an illegal value making this input required</tr>
<tr><td align="right">routesoverlayfiles<td align="center">string_list<td align="center">None<td align="left">list of csv files to ammend the base routes file</tr>
<tr><td align="right">rundays<td align="center">int<td align="center">30<td align="left">Number of Days for Simulation</tr>
<tr><td align="right">saveall<td align="center">stringOrNone<td align="center">None<td align="left">filename for PKL file to save all graphs</tr>
<tr><td align="right">scaleadminstorage<td align="center">string<td align="center">nolongersupported<td align="left">this input is no longer supported</tr>
<tr><td align="right">scaleclinicstorage<td align="center">string<td align="center">nolongersupported<td align="left">this input is no longer supported</tr>
<tr><td align="right">scaledemandactual<td align="center">float<td align="center">1.0<td align="left">factor between 0 and 1 to scale the actual demand</tr>
<tr><td align="right">scaledemandbytypeactual<td align="center">string_list<td align="center">None<td align="left">factor to scale expected demand by vaccine (and other) type.  Format is a comma-separated list of vax_a:scale pairs</tr>
<tr><td align="right">scaledemandbytypeexpected<td align="center">string_list<td align="center">None<td align="left">factor to scale expected demand by vaccine (and other) type.  Format is a comma-separated list of vax_a:scale pairs</tr>
<tr><td align="right">scaledemandexpected<td align="center">float<td align="center">1.0<td align="left">factor between 0 and 1 to scale the expected demand</tr>
<tr><td align="right">scalenumberoftrucks<td align="center">string<td align="center">nolongersupported<td align="left">this input is no longer supported</tr>
<tr><td align="right">seed<td align="center">longOrNone<td align="center">None<td align="left">set random seed</tr>
<tr><td align="right">shippingcalendarfile<td align="center">stringOrNone<td align="center">None<td align="left">filename for specifying the calendar demand for shipping calculations</tr>
<tr><td align="right">shippingdelayseed<td align="center">longOrNone<td align="center">None<td align="left">if exists use a separate random number generator seeded with this value for any shipping delay processes not explicitly overridden in the routes file</tr>
<tr><td align="right">shippingdemandfile<td align="center">stringOrNone<td align="center">None<td align="left">file defining the demand for shipping quantity calculations used in the model</tr>
<tr><td align="right">stockmonitorinterval<td align="center">float<td align="center">0.1<td align="left">interval to monitor stock at each store to look for overstocking</tr>
<tr><td align="right">stockmonitorthresh<td align="center">float<td align="center">0.99<td align="left">Threshold for recording an overstocking</tr>
<tr><td align="right">storagebreakage<td align="center">float_list<td align="center">0.0<td align="left">transit breakage fraction (one value per level).  If insufficient values specified the last value is copied.</tr>
<tr><td align="right">storesfile<td align="center">string<td align="center">None<td align="left">filename defining the models storage units. Default of None is an illegal value making this input required</tr>
<tr><td align="right">storesoverlayfiles<td align="center">string_list<td align="center">None<td align="left">list of csv files to ammend the base stores file</tr>
<tr><td align="right">tally<td align="center">string_list<td align="center">None<td align="left">histogram this warehouse</tr>
<tr><td align="right">targetpopulationyear<td align="center">int<td align="center">-1<td align="left">The year in which the population should be extrapolated to</tr>
<tr><td align="right">trackshipment<td align="center">long<td align="center">0<td align="left">when tracking a vial of vaccine select it from this factory shipment</tr>
<tr><td align="right">trackvial<td align="center">stringOrNone<td align="center">None<td align="left">track a vial for this vaccine</tr>
<tr><td align="right">transitbreakage<td align="center">float_list<td align="center">0.0<td align="left">transit breakage fraction (one value per level).  If insufficient values specified the last value is copied.</tr>
<tr><td align="right">truckfile<td align="center">stringOrNone<td align="center">None<td align="left">file to define or override the unified truck type definitions</tr>
<tr><td align="right">twentyeightdaymonths<td align="center">TF<td align="center">False<td align="left">If true then months are 28 days long. False means 30 days. Weeks are always 7 days and years are always 12 months</tr>
<tr><td align="right">usebetanetwork<td align="center">TF<td align="center">False<td align="left">Use new network creation code</tr>
<tr><td align="right">usestaticdemand<td align="center">TF<td align="center">False<td align="left">If true the demand will not be stochastic but instead exactly what you put in Stores file which is only useful for debugging</tr>
<tr><td align="right">vaccinefile<td align="center">stringOrNone<td align="center">None<td align="left">file to define or override the unified vaccine type definitions</tr>
<tr><td align="right">verbose<td align="center">TF<td align="center">False<td align="left">turns on verbose output</tr>
<tr><td align="right">vizshapes<td align="center">string_list<td align="center">["'c'", "'s'", "'c'", "'s'"]<td align="left">gEarth visualization shapes (one val per level).  If insufficient values are specified then the last value is copied</tr>
<tr><td align="right">vizwidths<td align="center">float_list<td align="center">['0.1', '0.05', '0.03', '0.01']<td align="left">gEarth visualization widths (one val per level).  If insufficient values are specified then the last value is copied</tr>
<tr><td align="right">wasteestfreq<td align="center">int<td align="center">0<td align="left">how often to update the factory waste estimation algorithm</tr>
<tr><td align="right">wasteestupdatelatency<td align="center">float<td align="center">50.0<td align="left">latency until start-up of OVW update process</tr>

</table>
