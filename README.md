A set of tools I use to manage my ltspice and schematics. Barely usable for others now, but as soon as it is I will add
some documentation.


# ltmc.py - A montecarlo/minmax simulation generator
Take your existing simulation and transform it into a monte carlo like, or min/max tolerance simulation.

## Monte Carlo
The spe
## Min/Max

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

