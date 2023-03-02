A set of tools I use to manage my ltspice and schematics. Barely usable for others now, but as soon as it is I will add
some documentation.


# ltmc.py - A montecarlo/minmax simulation generator
Take your existing simulation and transform it into a monte carlo like, or min/max tolerance simulation.

## Monte Carlo
You should also specify the number of runs for this as it will use (pseudo)random numbers to have them deviate per run,
so you can chose how often you want to run it.
## Min/Max
By counting up a number and interpreting its bits as negative or positive tolerance indicators, this will test all
combinations of far extreme tolerances. Be aware of that this will end up in 2**N runs for N components, and since
ltspice itself only supports up to 100001, more than 16 components will not run. Given that usually a simulation runs
longer than a second, this will most likely run days anyways so isn't feasible.

## Specifying components and their tolerances

You can specify components like
```
ltmc.py -C R1 ltmc.asc
```

Without anything else, this will just select `R1` and checks its `tol` SpiceLine value. If thats not present, its an
error, unless you specify something else.

* `-C R1:4` will set the component value (likely R since it seems to be a resistor) tolerance to 4%
* `-C R1:R=4` alternative syntax explicitly chosing to set the resistance tolerance
* `-C C1:Rser=4` selects for component C1 the Rser (serial resistance) component and a tolerance of 4%.
* `-C C1:Rser=4,Rpar=10/20` selects C1 and sets Rser to 4% tolerance but RPar to 10/20 which means 10% lower and 20%
  higher tolerance

You can use multiple `-C` arguments or a list of them seperated by `;` but be careful that the shell does not interpret
it.

