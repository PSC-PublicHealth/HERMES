<p>Specify the number of times (instances) you wish to run the model when generating this set of results. 
Each instance will generate somewhat different results, due to stochasticity. 
To better capture the day-to-day variation that occurs in the real world, HERMES models are stochastic (unless otherwise specified in the parameters). 
For example, daily demand at an immunizing location is not uniform -- rather, some days will see more patients than others. 
Thus, HERMES stochastically generates daily demand as a Poisson distribution. 
</p><br>
<p>
To obtain results that are representative of the model, running multiple instances is recommended. 
Each model is different, but a good rule of thumb is to run 10 instances for results that will not vary significantly between runs. 
</p>