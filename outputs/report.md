# Farm waste-to-energy - Group 2 energy and TEA

## Summary (S3)

| metric                         |    value |
|:-------------------------------|---------:|
| Waste processed (wet t/yr)     |   146    |
| Methane (Nm3/yr)               | 16488.7  |
| Gross electricity (kWh/yr)     | 57404.8  |
| Net electricity (kWh/yr)       | 51664.3  |
| Useful recovered heat (kWh/yr) | 51664.8  |
| Overall efficiency (%)         |    63    |
| Electricity saving ($/yr)      | 13122.7  |
| Heat saving ($/yr)             |  3646.92 |
| CO2 avoided (t/yr)             |    48.32 |

## Energy balance

```
Energy in                      164,015kWh/yr
Gross useful output             57,405kWh/yr
of which own use                 5,740kWh/yr
Net electricity                 51,664kWh/yr
Recovered heat used             51,665kWh/yr
Loses                           54,946kWh/yr
Total out                      164,015kWh/yr
Closure error                    0.0%
Efficiency (gross)              66.5%
Efficiency (net)                63.0%
```

## Effect of waste composition

| composition        |   wet_kg_per_day |   vs_kg_per_day |   ch4_nm3_per_day |   electricity_kwh_per_year |   vs_first |
|:-------------------|-----------------:|----------------:|------------------:|---------------------------:|-----------:|
| Farm mix           |              400 |             108 |             45.17 |                    57404.8 |       0    |
| All food waste     |              400 |             100 |             43.03 |                    54675.4 |      -0.05 |
| Carbohydrate-heavy |              400 |             118 |             43.36 |                    55103.2 |      -0.04 |
| With oil           |              400 |             118 |             57.2  |                    72685.9 |       0.27 |
| All oil            |              400 |             380 |            305.01 |                   387590   |       5.75 |

## Alignment with Group 1

- Yield basis: methane per kg VS fed (Treated Yield / VS fed), as in formulas 22-23
- S3: 430.2 L CH4/kg VS used; Group 1's Specific Yield column says 285.1
- Group 1's Specific Yield column is not methane per kg VS fed (it is treated yield x stability / 2.5), so it is not used
- Food-waste VS share of wet weight: yours 0.250, Group 1 0.225
- Farm mix by VS (Group 1's SCG percentages are by VS): food_waste 74.1%, scg 25.9%
- Check: Group 1's own feed in your model gives 3.74 kWh/day of electricity vs their 3.37 (+11.1%, does not match)

## All scenarios

The farm's own waste run under each Group 1 scenario. Full columns are in all_scenarios.csv.

| Scenario ID   | Scenario                                     |   Yield multiplier |   Net electricity (kWh/yr) |   CO2 avoided (t/yr) |   Total Savings ($/yr) |   Net electricity vs S1 (%) | Notes                                                                   |
|:--------------|:---------------------------------------------|-------------------:|---------------------------:|---------------------:|-----------------------:|----------------------------:|:------------------------------------------------------------------------|
| S1            | Control food waste                           |              0.895 |                    46220.4 |               43.23  |                15002.6 |                       0     |                                                                         |
| S2            | Low fungal pretreatment                      |              0.939 |                    48515.4 |               45.376 |                15747.5 |                       4.965 |                                                                         |
| S3            | Moderate fungal pretreatment (Reference)     |              1     |                    51664.3 |               48.321 |                16769.7 |                      11.778 |                                                                         |
| S4            | High fungal pretreatment                     |              1.049 |                    54172.8 |               50.668 |                17583.9 |                      17.206 |                                                                         |
| S5            | Extended fungal pretreatment                 |              1.086 |                    56094.2 |               52.465 |                18207.6 |                      21.363 |                                                                         |
| S6            | Moderate pretreatment + 10% SCG              |              1     |                    51680.5 |               48.337 |                16774.9 |                      11.813 | different feedstock; only its process effect is applied to the farm mix |
| S7            | Moderate pretreatment + 20% SCG              |              1     |                    51648   |               48.306 |                16764.4 |                      11.743 | different feedstock; only its process effect is applied to the farm mix |
| S8            | Moderate pretreatment + 30% SCG              |              1     |                    51669.9 |               48.327 |                16771.5 |                      11.79  | different feedstock; only its process effect is applied to the farm mix |
| S9            | Moderate pretreatment + 10% SCG + high OLR   |              1     |                    51680.5 |               48.337 |                16774.9 |                      11.813 | different feedstock; only its process effect is applied to the farm mix |
| S10           | Carbohydrate-rich (Cooked Rice)              |              1     |                    51664.3 |               48.321 |                16769.7 |                      11.778 | different feedstock; only its process effect is applied to the farm mix |
| S11           | Protein-rich (Meat Waste)                    |              1     |                    51664.3 |               48.321 |                16769.7 |                      11.778 | different feedstock; only its process effect is applied to the farm mix |
| S12           | Lipid-rich (Plant Oil)                       |              1     |                    51664.3 |               48.321 |                16769.7 |                      11.778 | different feedstock; only its process effect is applied to the farm mix |
| S13           | Fibre-rich (Banana Peel)                     |              1     |                    51664.3 |               48.321 |                16769.7 |                      11.778 | different feedstock; only its process effect is applied to the farm mix |
| S14           | Acidogenic Bacterial Activity (+20%)         |              1.001 |                    51717.7 |               48.371 |                16787   |                      11.894 |                                                                         |
| S15           | Acetogenic Bacterial Activity (+20%)         |              1.001 |                    51717.7 |               48.371 |                16787   |                      11.894 |                                                                         |
| S16           | Acetoclastic Methanogenic Archaea (+20%)     |              1.112 |                    57428.5 |               53.713 |                18640.7 |                      24.249 | Group 1 energy columns don't match its yield; energy taken from yield   |
| S17           | Hydrogenotrophic Methanogenic Archaea (+20%) |              1     |                    51664.3 |               48.321 |                16769.7 |                      11.778 |                                                                         |
| S21           | Low biochar addition                         |              1.001 |                    51732.6 |               48.385 |                16791.8 |                      11.926 | effect from uncalibrated batch test                                     |
| S22           | Moderate biochar addition                    |              1.001 |                    51730.7 |               48.384 |                16791.2 |                      11.922 | effect from uncalibrated batch test                                     |
| S23           | High biochar addition                        |              1.001 |                    51710.9 |               48.365 |                16784.8 |                      11.879 | effect from uncalibrated batch test                                     |
| S24           | Reduced inoculum: S:I = 2                    |              0.975 |                    50347.6 |               47.09  |                16342.3 |                       8.929 | effect from uncalibrated batch test                                     |

## Data checks (for Group 1)

Not in the scenario file: s18, s19, s20.

These rows have energy columns that do not match their methane yield. The pipeline uses the yield and ignores those columns.

| Scenario ID   | check                           |   value |   expected |
|:--------------|:--------------------------------|--------:|-----------:|
| S16           | methane energy content (MJ/Nm3) |  32.217 |     35.808 |

## Status

These assumptions are still placeholders, so the numbers above are illustrative: chp, heat_recovery, emissions.

| section | source / who to ask |
| --- | --- |
| chp | need an engine sheet |
| heat_recovery | need digester heating demand and on-form heat use |
| emissions | find publisher and cite it |
