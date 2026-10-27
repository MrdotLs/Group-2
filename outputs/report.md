# Farm waste-to-energy - Group 2 energy and TEA

## Summary

| metric                         |    value |
|:-------------------------------|---------:|
| Waste processed (wet t/yr)     |   146    |
| Methane (Nm3/yr)               | 10920.3  |
| Gross electricity (kWh/yr)     | 38011.6  |
| Net electricity (kWh/yr)       | 34210.5  |
| Useful recovered heat (kWh/yr) | 34210.7  |
| Overall efficiency (%)         |    63    |
| Electricity saving ($/yr)      |  8689.46 |
| Heat saving ($/yr)             |  2414.88 |
| CO2 avoided (t/yr)             |    32    |

## Energy balance

```
Energy in                      108,606kWh/yr
Gross useful output             38,012kWh/yr
of which own use                 3,801kWh/yr
Net electricity                 34,210kWh/yr
Recovered heat used             34,211kWh/yr
Recovered heat used             36,383kWh/yr
Total out                      108,606kWh/yr
Closure error                    0.0%
Efficiency (gross)              66.5%
Efficiency (net)                63.0%
```

## Effect of waste composition

| composition        |   wet_kg_per_day |   vs_kg_per_day |   ch4_nm3_per_day |   electricity_kwh_per_year |   vs_first |
|:-------------------|-----------------:|----------------:|------------------:|---------------------------:|-----------:|
| Farm mix           |              400 |             108 |             29.92 |                    38011.6 |       0    |
| All food waste     |              400 |             100 |             28.51 |                    36216   |      -0.05 |
| Carbohydrate-heavy |              400 |             118 |             28.71 |                    36478.1 |      -0.04 |
| With oil           |              400 |             118 |             37.89 |                    48139.6 |       0.27 |
| All oil            |              400 |             380 |            202.07 |                   256732   |       5.75 |

## Status

These assumptions are still placeholders, so the numbers above are illustrative: chp, heat_recovery, emissions.

| section | source / who to ask |
| --- | --- |
| chp | need an engine sheet |
| heat_recovery | need digester heating demand and on-form heat use |
| emissions | find publisher and cite it |
